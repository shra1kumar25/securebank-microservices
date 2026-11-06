from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    customer_id: int
    reference: str
    event_type: str
    message: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
