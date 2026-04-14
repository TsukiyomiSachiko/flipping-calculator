# Backend Setup Guide

This guide covers setting up the **Flipping Calculator API** on a Linux server (e.g., Ubuntu/Debian) or local development machine.

## 📋 Prerequisites

### System Requirements
*   **OS:** Ubuntu 20.04+ / Debian 11+ (Recommended for Mini PC/Server)
*   **Python:** 3.10+
*   **Database:** PostgreSQL 13+

### 1. Install System Dependencies
Update your package list and install Python, pip, and PostgreSQL.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib libpq-dev git
```

### 2. Configure PostgreSQL
Create a database and user for the application.

```bash
# Switch to postgres user
sudo -i -u postgres

# Enter SQL prompt
psql
```

Inside the `psql` shell:

```sql
-- Create database
CREATE DATABASE osrs_flipping;

-- Create user with password
CREATE USER flipping_user WITH PASSWORD 'flipping_dev_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE osrs_flipping TO flipping_user;
-- For Postgres 15+ you also need:
\c osrs_flipping
GRANT ALL ON SCHEMA public TO flipping_user;

-- Exit
\q
```

Exit the postgres user session:
```bash
exit
```

## 🚀 Installation

### 1. Set Up Python Environment

Navigate to the API directory:

```bash
cd flipping-calculator-api
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Python Packages

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file (optional, but recommended for overriding defaults) or just export the variable. The default config looks for a local Postgres instance.

**Default Database URL:** `postgresql://flipping_user:flipping_dev_password@localhost/osrs_flipping`

To change it, run:
```bash
export DATABASE_URL="postgresql://your_user:your_password@localhost/your_db"
```

## 🏃‍♂️ Running the Server

### Option A: Development (Auto-reload)
Use the provided script for local development.

```bash
./run.sh
```
*   **URL:** `http://localhost:8000`
*   **Docs:** `http://localhost:8000/docs`

### Option B: Production (Mini PC / Server)
For a dedicated server, run without auto-reload to save resources.

```bash
# Activate venv if not active
source venv/bin/activate

# Run with 4 workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Option C: Systemd Service (Recommended for 24/7)
To keep the app running in the background and restart on boot:

1.  Create a service file: `sudo nano /etc/systemd/system/osrs-api.service`

```ini
[Unit]
Description=OSRS Flipping Calculator API
After=network.target postgresql.service

[Service]
User=YOUR_USERNAME
WorkingDirectory=/path/to/flipping-calculator/flipping-calculator-api
ExecStart=/path/to/flipping-calculator/flipping-calculator-api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

2.  Enable and start:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable osrs-api
    sudo systemctl start osrs-api
    ```

## 🛠️ First-Time Initialization

Once the server is running, you **must** sync the item database:

```bash
curl -X POST http://localhost:8000/api/items/sync
```

This will download ~4,500 items from the Wiki API to your local PostgreSQL database.

## 🐳 Docker Setup (Alternative)

If you prefer keeping your system clean, use Docker.

1.  **Build Image:**
    ```bash
    docker build -t osrs-api .
    ```

2.  **Run Container:**
    ```bash
    docker run -d 
      -p 8000:8000 
      --name osrs-api 
      -e DATABASE_URL="postgresql://user:pass@host.docker.internal/db" 
      osrs-api
    ```
    *(Note: You'll need a Docker network or external DB for persistence)*

## 🔍 Troubleshooting

*   **Database Connection Failed:**
    *   Check if Postgres is running: `sudo systemctl status postgresql`
    *   Verify credentials in `app/utils/database.py` or `DATABASE_URL` env var.
*   **Dependencies Missing:**
    *   Ensure you installed `libpq-dev` (required for `psycopg2`).
