from datetime import date, datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel

class ProviderSyncRequest(BaseModel):
    npi: str

class ProviderBase(BaseModel):
    npi: Optional[str] = None
    full_name: str
    dept: Optional[str] = None
    location: Optional[str] = None
    primary_specialty: Optional[str] = None
    is_active: bool = True

class ProviderCreate(ProviderBase):
    pass

class ProviderResponse(ProviderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CredentialBase(BaseModel):
    type: str
    issuer: str
    number: str
    status: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_verified_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None

class CredentialCreateOrUpdate(BaseModel):
    provider_id: int
    type: str
    issuer: str
    number: str
    expiry_date: Optional[date] = None
    # Assuming other fields are optional or have defaults for update logic

class CredentialResponse(CredentialBase):
    id: int
    provider_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExpiringCredentialsRequest(BaseModel):
    window_days: int
    dept: Optional[str] = None
    location: Optional[str] = None

class ExpiringCredentialResult(BaseModel):
    provider: ProviderResponse
    credential: CredentialResponse
    days_to_expiry: int
    risk_score: float # calculated somehow?

class ProviderSnapshotRequest(BaseModel):
    provider_id: Optional[int] = None
    npi: Optional[str] = None

class ProviderSnapshotResponse(BaseModel):
    provider: ProviderResponse
    credentials: List[CredentialResponse]
