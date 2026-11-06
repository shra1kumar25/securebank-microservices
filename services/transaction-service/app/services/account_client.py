import httpx
from fastapi import HTTPException

from app.core.config import settings


def adjust_balance(
    account_id: int,
    amount: str,
    operation: str,
    token: str,
) -> dict:
    url = f"{settings.ACCOUNT_SERVICE_URL}/api/v1/accounts/{account_id}/{operation}"

    try:
        response = httpx.post(
            url,
            json={"amount": amount},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Account Service is unavailable",
        ) from exc

    if response.is_error:
        try:
            detail = response.json().get("detail", "Account operation failed")
        except ValueError:
            detail = "Account operation failed"

        code = response.status_code if response.status_code < 500 else 502
        raise HTTPException(status_code=code, detail=detail)

    return response.json()
