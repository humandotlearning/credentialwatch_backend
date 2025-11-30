# CredentialWatch Backend 🩺⚙️

This repository contains the backend services for **CredentialWatch**, a demo product for the "MCP 1st Birthday / Gradio Agents Hackathon".

CredentialWatch is a system designed to manage and monitor healthcare provider credentials, providing a unified view and proactive alerts for expiries.

## 🏗 Architecture

The CredentialWatch system consists of:

1.  **Modal Backend (This Repo)**:
    -   FastAPI microservices running on Modal.
    -   SQLite database (`credentialwatch.db`) on a Modal volume.
    -   Exposes APIs for NPI data, Credential management, and Alerts.
2.  **MCP Servers**: Three separate Model Context Protocol servers (`npi_mcp`, `cred_db_mcp`, `alert_mcp`) that interface with the Modal backend.
3.  **Agent & UI**: A LangGraph agent and Gradio UI (hosted on Hugging Face Spaces) that interact with the MCP servers.

## 🧱 Tech Stack

-   **Language**: Python 3.11
-   **Package Management**: `uv`
-   **Framework**: FastAPI
-   **Infrastructure**: Modal
-   **Database**: SQLite (with SQLAlchemy 2.x)

## 📂 Project Structure

```text
src/credentialwatch_backend/
├── app_npi.py       # NPI Registry Proxy API
├── app_cred.py      # Provider & Credential Management API
├── app_alert.py     # Alert Management API
├── db.py            # Database connection & session
├── init_db.py       # DB initialization & seeding script
├── models.py        # SQLAlchemy models
└── schemas_*.py     # Pydantic schemas
```

## 🚀 Setup & Usage

### Prerequisites

-   Python 3.11+
-   `uv` (recommended) or `pip`
-   Modal account and CLI configured (`modal setup`)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/credentialwatch-backend.git
cd credentialwatch-backend

# Install dependencies
uv sync
# OR
pip install -e .
```

### Database Initialization

To create the database tables and seed with demo data:

```bash
python -m src.credentialwatch_backend.init_db
```

This will create a `credentialwatch.db` file in the current directory (for local development).

### Running the Services

You can run the FastAPI services locally using `uvicorn`:

```bash
# NPI API
uvicorn src.credentialwatch_backend.app_npi:app --reload --port 8001

# Credential API
uvicorn src.credentialwatch_backend.app_cred:app --reload --port 8002

# Alert API
uvicorn src.credentialwatch_backend.app_alert:app --reload --port 8003
```

### Deploying to Modal

To deploy the backend to Modal:

1.  **Initialize the Database on Modal Volume**:
    ```bash
    modal run src.credentialwatch_backend.modal_app::init_db
    ```

2.  **Serve the App (Dev Mode)**:
    ```bash
    modal serve src.credentialwatch_backend.modal_app
    ```

3.  **Deploy to Production**:
    ```bash
    modal deploy src.credentialwatch_backend.modal_app
    ```

The API will be available at the URL provided by Modal (e.g., `https://your-username--credentialwatch-backend-fastapi-app.modal.run`).

The endpoints are mounted as follows:
-   `/cred`: Credential Management API
-   `/npi`: NPI Registry Proxy API
-   `/alert`: Alert Management API

## 🗄️ Database Schema

-   **Providers**: Stores provider info (NPI, name, department, location).
-   **Credentials**: Stores licenses, board certs, etc., with expiry dates.
-   **Alerts**: Stores generated alerts for expiring credentials.

## 🧪 Testing

```bash
# Run tests
pytest
```
