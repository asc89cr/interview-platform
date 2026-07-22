"""Stripe SDK wrapper.

All Stripe interactions go through this module so the rest of the codebase
stays free of direct stripe.* calls and is easier to mock in tests.

Required environment variables:
    STRIPE_SECRET_KEY        — sk_test_… or sk_live_…
    STRIPE_WEBHOOK_SECRET    — whsec_…
    STRIPE_PRO_PRICE_ID      — price_… for the Pro monthly plan
    STRIPE_TEAMS_PRICE_ID    — price_… for the Teams monthly plan
"""
import os

import stripe as _stripe

_stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
PRO_PRICE_ID: str = os.getenv("STRIPE_PRO_PRICE_ID", "")
TEAMS_PRICE_ID: str = os.getenv("STRIPE_TEAMS_PRICE_ID", "")


def create_or_get_customer(email: str, name: str) -> str:
    """Return an existing Stripe customer ID or create a new one."""
    customers = _stripe.Customer.list(email=email, limit=1)
    if customers.data:
        return customers.data[0].id
    customer = _stripe.Customer.create(email=email, name=name)
    return customer.id


def create_checkout_session(
    customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    tier: str,
) -> _stripe.checkout.Session:
    return _stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        # Embed the tier so the webhook can set subscription_tier correctly
        metadata={"tier": tier},
    )


def create_billing_portal_session(customer_id: str, return_url: str) -> _stripe.billing_portal.Session:
    return _stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )


def construct_webhook_event(payload: bytes, sig_header: str) -> _stripe.Event:
    """Verify the Stripe signature and parse the event payload."""
    return _stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
