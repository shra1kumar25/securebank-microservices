from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_customer
from app.db.database import get_db
from app.models.transaction import (
    Transaction,
    TransactionStatus,
    TransactionType,
)
from app.schemas.transaction import (
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawalRequest,
)
from app.services.account_client import adjust_balance
from app.services.event_publisher import publish_transaction_event

router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["Transactions"],
)


def save_transaction(
    db: Session,
    customer_id: int,
    transaction_type: TransactionType,
    amount: Decimal,
    from_account_id: int | None = None,
    to_account_id: int | None = None,
    transaction_status: TransactionStatus = TransactionStatus.SUCCESS,
) -> Transaction:
    transaction = Transaction(
        reference=f"SB-{uuid4().hex[:16].upper()}",
        customer_id=customer_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        transaction_type=transaction_type,
        amount=amount,
        currency="INR",
        status=transaction_status,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def notify_transaction(transaction: Transaction) -> Transaction:
    event_type = transaction.transaction_type.value
    transaction_status = transaction.status.value

    message = (
        f"{event_type.title()} of {transaction.currency} "
        f"{transaction.amount:.2f} was {transaction_status.lower()}. "
        f"Reference: {transaction.reference}"
    )

    event = {
        "event_type": event_type,
        "customer_id": transaction.customer_id,
        "reference": transaction.reference,
        "amount": str(transaction.amount),
        "currency": transaction.currency,
        "status": transaction_status,
        "from_account_id": transaction.from_account_id,
        "to_account_id": transaction.to_account_id,
        "message": message,
    }

    publish_transaction_event(event)

    return transaction


@router.post(
    "/deposit",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def deposit(
    data: DepositRequest,
    db: Session = Depends(get_db),  # noqa: B008
    customer: dict = Depends(get_current_customer),  # noqa: B008
):
    adjust_balance(
        data.account_id,
        str(data.amount),
        "credit",
        customer["token"],
    )

    transaction = save_transaction(
        db,
        customer["customer_id"],
        TransactionType.DEPOSIT,
        data.amount,
        to_account_id=data.account_id,
    )

    return notify_transaction(transaction)


@router.post(
    "/withdraw",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def withdraw(
    data: WithdrawalRequest,
    db: Session = Depends(get_db),  # noqa: B008
    customer: dict = Depends(get_current_customer),  # noqa: B008
):
    adjust_balance(
        data.account_id,
        str(data.amount),
        "debit",
        customer["token"],
    )

    transaction = save_transaction(
        db,
        customer["customer_id"],
        TransactionType.WITHDRAWAL,
        data.amount,
        from_account_id=data.account_id,
    )

    return notify_transaction(transaction)


@router.post(
    "/transfer",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def transfer(
    data: TransferRequest,
    db: Session = Depends(get_db),  # noqa: B008
    customer: dict = Depends(get_current_customer),  # noqa: B008
):
    if data.from_account_id == data.to_account_id:
        raise HTTPException(
            status_code=400,
            detail="Source and destination accounts must be different",
        )

    token = customer["token"]

    adjust_balance(
        data.from_account_id,
        str(data.amount),
        "debit",
        token,
    )

    try:
        adjust_balance(
            data.to_account_id,
            str(data.amount),
            "credit",
            token,
        )
    except HTTPException:
        try:
            adjust_balance(
                data.from_account_id,
                str(data.amount),
                "credit",
                token,
            )
        except HTTPException as compensation_error:
            failed_transaction = save_transaction(
                db,
                customer["customer_id"],
                TransactionType.TRANSFER,
                data.amount,
                from_account_id=data.from_account_id,
                to_account_id=data.to_account_id,
                transaction_status=TransactionStatus.FAILED,
            )

            notify_transaction(failed_transaction)

            raise HTTPException(
                status_code=502,
                detail=(
                    "Transfer failed and automatic compensation also failed. "
                    "Manual reconciliation is required."
                ),
            ) from compensation_error

        failed_transaction = save_transaction(
            db,
            customer["customer_id"],
            TransactionType.TRANSFER,
            data.amount,
            from_account_id=data.from_account_id,
            to_account_id=data.to_account_id,
            transaction_status=TransactionStatus.FAILED,
        )

        notify_transaction(failed_transaction)

        raise

    transaction = save_transaction(
        db,
        customer["customer_id"],
        TransactionType.TRANSFER,
        data.amount,
        from_account_id=data.from_account_id,
        to_account_id=data.to_account_id,
    )

    return notify_transaction(transaction)


@router.get("", response_model=list[TransactionResponse])
def transaction_history(
    db: Session = Depends(get_db),  # noqa: B008
    customer: dict = Depends(get_current_customer),  # noqa: B008
):
    return (
        db.query(Transaction)
        .filter(Transaction.customer_id == customer["customer_id"])
        .order_by(Transaction.created_at.desc())
        .all()
    )
