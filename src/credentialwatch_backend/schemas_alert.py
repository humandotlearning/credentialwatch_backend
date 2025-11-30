from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class AlertCreate(BaseModel):
    provider_id: int
    credential_id: Optional[int] = None
    severity: str
    window_days: int
    message: str
    channel: Optional[str] = "ui"

class AlertResolve(BaseModel):
    resolution_note: Optional[str] = None

class AlertResponse(BaseModel):
    id: int
    provider_id: int
    credential_id: Optional[int] = None
    severity: str
    window_days: int
    message: str
    channel: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None

    class Config:
        from_attributes = True

class AlertSummaryRequest(BaseModel):
    window_days: Optional[int] = None
