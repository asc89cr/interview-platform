# Build Agent 02 — Auth & Payments Agent

## Mission
Implement user registration, login, JWT authentication, and Stripe subscription
billing. Enforces subscription tier limits across all protected endpoints.

---

## Run Order
**Depends on:** Database Agent (01)
**Must complete before:** Backend API Agent, Web Dashboard Agent

---

## Tech Stack
- FastAPI (dependency injection for auth)
- python-jose (JWT creation + validation)
- passlib + bcrypt (password hashing)
- Stripe Python SDK
- httpx (webhook verification)

---

## Owns These Files
```
backend/
├── auth/
│   ├── jwt.py           # Token creation, decoding, refresh
│   ├── dependencies.py  # get_current_user() FastAPI dependency
│   └── router.py        # /auth/register, /auth/login, /auth/refresh
├── billing/
│   ├── stripe_client.py # Stripe SDK wrapper
│   ├── router.py        # /billing/checkout, /billing/portal, /billing/webhook
│   └── limits.py        # Tier enforcement: check_session_limit(), check_analysis_allowed()
```

---

## Auth Endpoints to Implement

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account, return access + refresh tokens |
| POST | `/auth/login` | Validate credentials, return tokens |
| POST | `/auth/refresh` | Exchange refresh token for new access token |
| POST | `/auth/logout` | Invalidate refresh token |

## Billing Endpoints to Implement

| Method | Path | Description |
|--------|------|-------------|
| POST | `/billing/checkout` | Create Stripe Checkout session for Pro/Teams |
| GET | `/billing/portal` | Redirect to Stripe customer portal (cancel, upgrade) |
| POST | `/billing/webhook` | Receive Stripe events, update subscription_tier in DB |

---

## Subscription Tiers & Limits

```python
TIER_LIMITS = {
    "free": {
        "sessions_per_month": 3,
        "analysis_reports": False,
        "interviewer_profiles": 1,
    },
    "pro": {
        "sessions_per_month": None,   # unlimited
        "analysis_reports": True,
        "interviewer_profiles": None,
    },
    "teams": {
        "sessions_per_month": None,
        "analysis_reports": True,
        "interviewer_profiles": None,
        "pdf_export": True,
        "team_members": 10,
    },
}
```

---

## Stripe Webhook Events to Handle
- `checkout.session.completed` → activate subscription, update tier
- `invoice.payment_succeeded` → renew subscription
- `invoice.payment_failed` → downgrade to free, notify user
- `customer.subscription.deleted` → downgrade to free

---

## Deliverables
- [ ] Register + login endpoints with bcrypt password hashing
- [ ] JWT access token (15 min) + refresh token (30 days)
- [ ] `get_current_user()` FastAPI dependency used across all protected routes
- [ ] Stripe Checkout + webhook handler
- [ ] `check_session_limit()` and `check_analysis_allowed()` enforcement functions
- [ ] Unit tests for token creation/validation and tier limit logic

---

## Definition of Done
A user can register, log in, get a JWT, subscribe via Stripe test mode,
and the tier limits are enforced on protected endpoints.
