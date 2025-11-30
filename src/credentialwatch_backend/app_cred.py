from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from .db import get_db
from .models import Provider, Credential
from .schemas_cred import (
    ProviderSyncRequest, ProviderResponse, CredentialCreateOrUpdate, CredentialResponse,
    ExpiringCredentialsRequest, ExpiringCredentialResult, ProviderSnapshotRequest, ProviderSnapshotResponse
)
# In a real microservice setup, we might call NPI_API via HTTP.
# For simplicity/monolith within Modal, we can import the logic or assume the URL.
# Let's assume we call it via HTTP if it's a separate service,
# OR import if we treat them as modules.
# The prompt says "Calls NPI_API internally or uses passed payload".
# I'll simulate an internal call by importing the function logic or using a helper.
# But `app_npi.get_provider` is an async route handler.
# Let's use httpx to call it if it were deployed, but here I'll just use the NPPES logic directly
# or copy the relevant fetch logic to avoid circular deps or complex setup for now.
# Actually, calling the other app directly is cleaner if they are in the same repo.
import httpx
# We'll assume the NPI_API is running locally or accessible.
# For this code to work "out of the box" in tests, mocking or direct calls is better.
# Let's rely on the assumption that we can use `app_npi` functions if we wrap them properly,
# but `app_npi` defines `app` at module level.
from .app_npi import get_provider as fetch_npi_data

app = FastAPI(title="CRED_API")

@app.post("/providers/sync_from_npi", response_model=ProviderResponse)
async def sync_provider_from_npi(req: ProviderSyncRequest, db: Session = Depends(get_db)):
    # 1. Check if provider exists
    stmt = select(Provider).where(Provider.npi == req.npi)
    provider = db.execute(stmt).scalars().first()

    # 2. Fetch data from NPI API (using our internal function logic directly)
    try:
        npi_data = await fetch_npi_data(req.npi)
    except HTTPException as e:
        if e.status_code == 404:
             raise HTTPException(status_code=404, detail="NPI not found in registry")
        raise e

    # 3. Upsert
    if not provider:
        provider = Provider(
            npi=req.npi,
            full_name=npi_data.full_name,
            # basic mapping
            is_active=True
        )
        db.add(provider)
    else:
        provider.full_name = npi_data.full_name
        # update other fields...

    # Extract location from addresses if possible
    # npi_data.addresses has list of ProviderAddress
    primary_addr = next((a for a in npi_data.addresses), None) # just grab first for now
    if primary_addr:
        # Simplistic location string
        provider.location = f"{primary_addr.city}, {primary_addr.state}"

    # Extract specialty
    # npi_data.taxonomies
    primary_tax = next((t for t in npi_data.taxonomies if t.primary), None)
    if primary_tax:
        provider.primary_specialty = primary_tax.desc

    db.commit()
    db.refresh(provider)
    return provider

@app.post("/credentials/add_or_update", response_model=CredentialResponse)
def add_or_update_credential(cred: CredentialCreateOrUpdate, db: Session = Depends(get_db)):
    # Check if provider exists
    provider = db.get(Provider, cred.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Try to find existing credential by (provider_id, type, number)
    stmt = select(Credential).where(
        Credential.provider_id == cred.provider_id,
        Credential.type == cred.type,
        Credential.number == cred.number
    )
    existing_cred = db.execute(stmt).scalars().first()

    status = "active" # Default logic
    # simplistic status logic based on expiry
    if cred.expiry_date and cred.expiry_date < date.today():
        status = "expired"

    if existing_cred:
        existing_cred.issuer = cred.issuer
        existing_cred.expiry_date = cred.expiry_date
        existing_cred.status = status
        existing_cred.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_cred)
        return existing_cred
    else:
        new_cred = Credential(
            provider_id=cred.provider_id,
            type=cred.type,
            issuer=cred.issuer,
            number=cred.number,
            status=status,
            expiry_date=cred.expiry_date,
            issue_date=None, # Not in input
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_cred)
        db.commit()
        db.refresh(new_cred)
        return new_cred

@app.post("/credentials/expiring", response_model=List[ExpiringCredentialResult])
def get_expiring_credentials(req: ExpiringCredentialsRequest, db: Session = Depends(get_db)):
    target_date = date.today() + timedelta(days=req.window_days)

    stmt = select(Credential).join(Provider).where(
        Credential.status == "active",
        Credential.expiry_date <= target_date,
        # Credential.expiry_date >= date.today() # Optional: do we show already expired? "expiry_date <= now + window" implies expired too
    )

    if req.dept:
        stmt = stmt.where(Provider.dept == req.dept)
    if req.location:
        # Simple contains match
        stmt = stmt.where(Provider.location.contains(req.location))

    results = db.execute(stmt).scalars().all()

    output = []
    for cred in results:
        days = (cred.expiry_date - date.today()).days if cred.expiry_date else 0
        risk = 1.0 if days < 30 else 0.5 # Dummy risk logic

        output.append(ExpiringCredentialResult(
            provider=cred.provider,
            credential=cred,
            days_to_expiry=days,
            risk_score=risk
        ))
    return output

@app.post("/providers/snapshot", response_model=ProviderSnapshotResponse)
def get_provider_snapshot(req: ProviderSnapshotRequest, db: Session = Depends(get_db)):
    stmt = select(Provider)
    if req.provider_id:
        stmt = stmt.where(Provider.id == req.provider_id)
    elif req.npi:
        stmt = stmt.where(Provider.npi == req.npi)
    else:
        raise HTTPException(status_code=400, detail="Must provide provider_id or npi")

    provider = db.execute(stmt).scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Lazy load credentials
    creds = provider.credentials

    return ProviderSnapshotResponse(
        provider=provider,
        credentials=creds
    )
