from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.account import AccountStatus, AccountType


class AccountCreate(BaseModel):
    account_type: AccountType


class AccountResponse(BaseModel):
    id: int
    account_number: str
    customer_id: int
    account_type: AccountType
    balance: Decimal
    currency: str
    status: AccountStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BalanceResponse(BaseModel):
    account_number: str
    balance: Decimal
    currency: str
