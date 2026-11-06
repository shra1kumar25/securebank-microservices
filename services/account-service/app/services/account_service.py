import secrets
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account, AccountStatus, AccountType


def generate_account_number(db: Session) -> str:
    for _ in range(10):
        account_number = str(secrets.randbelow(10**12)).zfill(12)
        existing = (
            db.query(Account).filter(Account.account_number == account_number).first()
        )
        if existing is None:
            return account_number

    raise RuntimeError("Unable to generate a unique account number")


def create_account(
    db: Session,
    customer_id: int,
    account_type: AccountType,
) -> Account:
    account = Account(
        account_number=generate_account_number(db),
        customer_id=customer_id,
        account_type=account_type,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_customer_accounts(db: Session, customer_id: int) -> list[Account]:
    return db.query(Account).filter(Account.customer_id == customer_id).all()


def get_customer_account(
    db: Session,
    customer_id: int,
    account_id: int,
) -> Account | None:
    return (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.customer_id == customer_id,
        )
        .first()
    )


def adjust_account_balance(
    db: Session,
    customer_id: int,
    account_id: int,
    amount: Decimal,
    operation: str,
) -> Account:
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.customer_id == customer_id,
        )
        .with_for_update()
        .first()
    )

    if account is None:
        raise ValueError("Account not found")

    if account.status != AccountStatus.ACTIVE:
        raise ValueError("Account is not active")

    if operation == "DEBIT":
        if account.balance < amount:
            raise ValueError("Insufficient account balance")
        account.balance -= amount
    elif operation == "CREDIT":
        account.balance += amount
    else:
        raise ValueError("Invalid balance operation")

    db.commit()
    db.refresh(account)
    return account
