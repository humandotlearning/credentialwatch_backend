import modal
import os
from fastapi import FastAPI

# Define the image
image = modal.Image.debian_slim().pip_install(
    "fastapi",
    "sqlalchemy",
    "uvicorn",
    "httpx",
    "pydantic"
).env({"DATABASE_URL": "sqlite:////data/credentialwatch.db"})

app = modal.App("credentialwatch-backend")
volume = modal.Volume.from_name("credentialwatch-data", create_if_missing=True)

@app.function(image=image, volumes={"/data": volume})
@modal.asgi_app()
def fastapi_app():
    # Import apps here to ensure they pick up the env var (although set in image env)
    from .app_cred import app as cred_app
    from .app_npi import app as npi_app
    from .app_alert import app as alert_app
    
    main_app = FastAPI(title="CredentialWatch Backend")
    
    main_app.mount("/cred", cred_app)
    main_app.mount("/npi", npi_app)
    main_app.mount("/alert", alert_app)
    
    return main_app

@app.function(image=image, volumes={"/data": volume})
def init_db():
    # This function can be run manually to seed the DB
    from .init_db import create_all, seed_data
    print("Initializing database...")
    create_all()
    seed_data()
    print("Database initialized.")
