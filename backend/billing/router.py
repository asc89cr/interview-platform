"""Billing endpoints: /billing/checkout, /billing/portal, /billing/webhook."""
import os

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.billing import stripe_client
from backend.db.base import get_db
from backend.db.models.user import User

router = APIRouter(prefix="/billing", tags=["billing"])

_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
_VALID_TIERS = {"pro", "teams"}


# ── Request schemas ────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    tier: str  # "pro" | "teams"


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/checkout", summary="Create a Stripe Checkout session for Pro or Teams")
async def create_checkout(
    body: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if body.tier not in _VALID_TIERS:
        raise HTTPException(status_code=400, detail="tier must be 'pro' or 'teams'")

    # Lazily provision a Stripe customer on first checkout
    if not user.stripe_customer_id:
        customer_id = stripe_client.create_or_get_customer(user.email, user.name)
        user.stripe_customer_id = customer_id
        await db.flush()
    else:
        customer_id = user.stripe_customer_id

    price_id = (
        stripe_client.PRO_PRICE_ID if body.tier == "pro" else stripe_client.TEAMS_PRICE_ID
    )
    session = stripe_client.create_checkout_session(
        customer_id=customer_id,
        price_id=price_id,
        success_url=f"{_FRONTEND_URL}/billing/success",
        cancel_url=f"{_FRONTEND_URL}/billing/cancel",
        tier=body.tier,
    )
    return {"checkout_url": session.url}


@router.get("/portal", summary="Redirect to the Stripe customer portal")
async def billing_portal(user: User = Depends(get_current_user)) -> dict:
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer linked to this account",
        )
    portal = stripe_client.create_billing_portal_session(
        customer_id=user.stripe_customer_id,
        return_url=f"{_FRONTEND_URL}/settings",
    )
    return {"portal_url": portal.url}


@router.post("/webhook", status_code=status.HTTP_200_OK, summary="Receive Stripe events")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(None, alias="stripe-signature"),
) -> dict:
    payload = await request.body()
    try:
        event = stripe_client.construct_webhook_event(payload, stripe_signature)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Webhook error: {exc}")

    event_type: str = event["type"]
    obj: dict = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, obj)

    elif event_type == "invoice.payment_succeeded":
        await _handle_payment_succeeded(db, obj)

    elif event_type in ("invoice.payment_failed", "customer.subscription.deleted"):
        await _handle_downgrade(db, obj)

    return {"received": True}


# ── Webhook helpers ────────────────────────────────────────────────────────────

async def _get_user_by_customer(db: AsyncSession, customer_id: str) -> User | None:
    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    return result.scalar_one_or_none()


async def _handle_checkout_completed(db: AsyncSession, obj: dict) -> None:
    customer_id: str = obj.get("customer", "")
    subscription_id: str = obj.get("subscription", "")
    tier: str = obj.get("metadata", {}).get("tier", "pro")

    user = await _get_user_by_customer(db, customer_id)
    if user:
        user.subscription_tier = tier
        user.stripe_subscription_id = subscription_id
        await db.flush()


async def _handle_payment_succeeded(db: AsyncSession, obj: dict) -> None:
    """Renewal: keep the tier active and update the subscription reference."""
    customer_id: str = obj.get("customer", "")
    subscription_id: str = obj.get("subscription", "")

    user = await _get_user_by_customer(db, customer_id)
    if user:
        user.stripe_subscription_id = subscription_id
        await db.flush()


async def _handle_downgrade(db: AsyncSession, obj: dict) -> None:
    """Payment failure or cancellation: revert user to the Free tier."""
    customer_id: str = obj.get("customer", "")

    user = await _get_user_by_customer(db, customer_id)
    if user:
        user.subscription_tier = "free"
        user.stripe_subscription_id = None
        await db.flush()
