import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import date, timedelta

from credentialwatch_backend.db import Base, get_db
from credentialwatch_backend.app_cred import app as app_cred
from credentialwatch_backend.app_alert import app as app_alert
from credentialwatch_backend.models import Provider, Credential, Alert

# Use in-memory SQLite with StaticPool to share connection across threads/sessions
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client_cred(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app_cred.dependency_overrides[get_db] = override_get_db
    return TestClient(app_cred)

@pytest.fixture(scope="function")
def client_alert(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app_alert.dependency_overrides[get_db] = override_get_db
    return TestClient(app_alert)

def test_credential_crud_and_expiry(client_cred, db_session):
    # 1. Create Provider manually
    p = Provider(full_name="Test Prov", npi="1111111111", is_active=True, location="Test City")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)

    # 2. Add Credentials manually
    # Expires in 10 days
    c1 = Credential(
        provider_id=p.id, type="lic", issuer="State", number="123", status="active",
        expiry_date=date.today() + timedelta(days=10)
    )
    # Expires in 100 days
    c2 = Credential(
        provider_id=p.id, type="dea", issuer="Fed", number="456", status="active",
        expiry_date=date.today() + timedelta(days=100)
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    # 3. Query expiring in 30 days
    resp = client_cred.post("/credentials/expiring", json={"window_days": 30})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 1
    assert data[0]["credential"]["number"] == "123"
    assert data[0]["days_to_expiry"] == 10

    # 4. Query expiring in 120 days
    resp = client_cred.post("/credentials/expiring", json={"window_days": 120})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 2

def test_alerts_lifecycle(client_alert, db_session):
    # Setup provider
    p = Provider(full_name="Alert Prov", npi="2222222222", is_active=True)
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p) # Ensure ID is available

    # 1. Create Alert
    resp = client_alert.post("/alerts", json={
        "provider_id": p.id,
        "severity": "critical",
        "window_days": 7,
        "message": "Urgent alert"
    })
    assert resp.status_code == 200, resp.text
    alert_id = resp.json()["id"]

    # 2. List Open Alerts
    resp = client_alert.get("/alerts/open")
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == alert_id

    # 3. Resolve Alert
    resp = client_alert.post(f"/alerts/{alert_id}/resolve", json={"resolution_note": "Fixed"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["resolved_at"] is not None

    # 4. List Open Alerts (should be empty)
    resp = client_alert.get("/alerts/open")
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 0
