from datetime import datetime, date, timedelta
from .db import engine, Base, SessionLocal
from .models import Provider, Credential, Alert

def create_all():
    Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()

    # Check if data exists
    if db.query(Provider).first():
        db.close()
        print("Data already seeded.")
        return

    # Providers
    p1 = Provider(
        npi="1234567890",
        full_name="Dr. Alice Smith",
        dept="Cardiology",
        location="New York, NY",
        primary_specialty="Cardiology",
        is_active=True
    )
    p2 = Provider(
        npi="0987654321",
        full_name="Dr. Bob Jones",
        dept="Pediatrics",
        location="Boston, MA",
        primary_specialty="Pediatrics",
        is_active=True
    )
    db.add_all([p1, p2])
    db.commit()

    # Credentials
    # Expiring soon
    c1 = Credential(
        provider_id=p1.id,
        type="state_license",
        issuer="NY State Board",
        number="NY-12345",
        status="active",
        expiry_date=date.today() + timedelta(days=15),
        created_at=datetime.utcnow()
    )
    # Active
    c2 = Credential(
        provider_id=p1.id,
        type="dea",
        issuer="DEA",
        number="DEA-999",
        status="active",
        expiry_date=date.today() + timedelta(days=300),
        created_at=datetime.utcnow()
    )
    # Expired
    c3 = Credential(
        provider_id=p2.id,
        type="state_license",
        issuer="MA State Board",
        number="MA-55555",
        status="expired",
        expiry_date=date.today() - timedelta(days=10),
        created_at=datetime.utcnow()
    )

    db.add_all([c1, c2, c3])
    db.commit()

    # Alerts
    a1 = Alert(
        provider_id=p1.id,
        credential_id=c1.id,
        severity="warning",
        window_days=30,
        message="License expiring in 15 days",
        created_at=datetime.utcnow()
    )

    db.add(a1)
    db.commit()
    db.close()
    print("Seeded demo data.")

if __name__ == "__main__":
    create_all()
    seed_data()
