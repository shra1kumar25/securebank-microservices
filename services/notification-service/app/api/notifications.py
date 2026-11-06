from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_customer
from app.db.database import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
)


@router.get("", response_model=list[NotificationResponse])
def get_notifications(
    customer_id: int = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    return (
        db.query(Notification)
        .filter(Notification.customer_id == customer_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
