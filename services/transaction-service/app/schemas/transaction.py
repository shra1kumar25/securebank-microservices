from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import TransactionStatus, TransactionType


class DepositRequest(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class WithdrawalRequest(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class TransactionResponse(BaseModel):
    id: int
    reference: str
    customer_id: int
    from_account_id: int | None
    to_account_id: int | None
    transaction_type: TransactionType
    amount: Decimal
    currency: str
    status: TransactionStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
