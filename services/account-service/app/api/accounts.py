from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_customer
from app.db.database import get_db
from app.schemas.account import AccountCreate, AccountResponse
from app.schemas.balance import BalanceAdjustment
from app.services.account_service import (
    adjust_account_balance,
    create_account,
    get_customer_account,
    get_customer_accounts,
)

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_customer_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_customer: dict = Depends(get_current_customer),
):
    return create_account(
        db=db,
        customer_id=current_customer["customer_id"],
        account_type=account_data.account_type,
    )


@router.get("", response_model=list[AccountResponse])
def list_customer_accounts(
    db: Session = Depends(get_db),
    current_customer: dict = Depends(get_current_customer),
):
    return get_customer_accounts(
        db=db,
        customer_id=current_customer["customer_id"],
    )


@router.get("/{account_id}", response_model=AccountResponse)
def read_customer_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_customer: dict = Depends(get_current_customer),
):
    account = get_customer_account(
        db=db,
        customer_id=current_customer["customer_id"],
        account_id=account_id,
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/{account_id}/credit", response_model=AccountResponse)
def credit_account(
    account_id: int,
    data: BalanceAdjustment,
    db: Session = Depends(get_db),
    current_customer: dict = Depends(get_current_customer),
):
    try:
        return adjust_account_balance(
            db,
            current_customer["customer_id"],
            account_id,
            data.amount,
            "CREDIT",
        )
    except ValueError as exc:
        code = 404 if str(exc) == "Account not found" else 400
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.post("/{account_id}/debit", response_model=AccountResponse)
def debit_account(
    account_id: int,
    data: BalanceAdjustment,
    db: Session = Depends(get_db),
    current_customer: dict = Depends(get_current_customer),
):
    try:
        return adjust_account_balance(
            db,
            current_customer["customer_id"],
            account_id,
            data.amount,
            "DEBIT",
        )
    except ValueError as exc:
        code = 404 if str(exc) == "Account not found" else 400
        raise HTTPException(status_code=code, detail=str(exc)) from exc
