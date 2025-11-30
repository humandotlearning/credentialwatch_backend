from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from .db import get_db
from .models import Alert, Provider, Credential
from .schemas_alert import AlertCreate, AlertResponse, AlertResolve, AlertSummaryRequest

app = FastAPI(title="ALERT_API")

@app.post("/alerts", response_model=AlertResponse)
def create_alert(alert_in: AlertCreate, db: Session = Depends(get_db)):
    # Verify provider exists
    if not db.get(Provider, alert_in.provider_id):
        raise HTTPException(status_code=404, detail="Provider not found")

    if alert_in.credential_id:
        if not db.get(Credential, alert_in.credential_id):
             raise HTTPException(status_code=404, detail="Credential not found")

    new_alert = Alert(
        provider_id=alert_in.provider_id,
        credential_id=alert_in.credential_id,
        severity=alert_in.severity,
        window_days=alert_in.window_days,
        message=alert_in.message,
        channel=alert_in.channel or "ui",
        created_at=datetime.utcnow()
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert

@app.get("/alerts/open", response_model=List[AlertResponse])
def get_open_alerts(
    provider_id: Optional[int] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    stmt = select(Alert).where(Alert.resolved_at == None)

    if provider_id:
        stmt = stmt.where(Alert.provider_id == provider_id)
    if severity:
        stmt = stmt.where(Alert.severity == severity)

    alerts = db.execute(stmt).scalars().all()
    return alerts

@app.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int, resolve_in: AlertResolve, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.resolved_at = datetime.utcnow()
    alert.resolution_note = resolve_in.resolution_note
    db.commit()
    db.refresh(alert)
    return alert

@app.post("/alerts/summary")
def get_alerts_summary(req: AlertSummaryRequest, db: Session = Depends(get_db)):
    # Simple count by severity
    # In real SQL we might do a group by
    from sqlalchemy import func

    stmt = select(Alert.severity, func.count(Alert.id)).where(Alert.resolved_at == None).group_by(Alert.severity)

    # If window_days is provided, filter by created_at...
    # (assuming window means "in the last X days"?)
    if req.window_days:
        start_date = datetime.utcnow() - timedelta(days=req.window_days)
        stmt = stmt.where(Alert.created_at >= start_date)

    results = db.execute(stmt).all()
    return {severity: count for severity, count in results}
