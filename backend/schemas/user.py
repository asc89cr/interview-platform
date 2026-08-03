import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    subscription_tier: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class UserWithStripe(UserRead):
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
