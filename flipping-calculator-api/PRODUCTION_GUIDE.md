# OSRS Flipping Calculator - Docker Production Guide

This guide details how to deploy the OSRS Flipping Calculator using Docker. This approach is ideal for running multiple applications on a single server as it isolates dependencies and configuration.

## 1. Prerequisites

Ensure your server has the following installed:
*   **Docker Engine** & **Docker Compose**
*   **Git**

### Installation (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to the docker group (avoids using sudo for docker commands)
sudo usermod -aG docker $USER
newgrp docker

# Install Git
sudo apt install git -y
```

## 2. Project Setup

Clone the repository to your server.

```bash
cd /home/your-user
git clone <your-repo-url> flipping-calculator
cd flipping-calculator
```

## 3. Configuration

### Database Credentials
The default `docker-compose.yml` uses:
*   User: `flipping_user`
*   Password: `flipping_password`
*   Database: `osrs_flipping`

**Recommended:** Change the password in `docker-compose.yml` before starting.
If you change it, update the `POSTGRES_PASSWORD` in the `db` service AND the password in the `DATABASE_URL` for the `backend` service.

### Port Configuration
The frontend is configured to run on port **3080** by default to avoid conflicts with other services you might have running on port 80.
To change this, edit `docker-compose.yml`:

```yaml
  frontend:
    ports:
      - "YOUR_PORT:80"
```

## 4. Deployment

Start the application stack in the background:

```bash
docker compose up -d --build
```

Check the status of your containers:

```bash
docker compose ps
```

View logs if needed:

```bash
docker compose logs -f
```

## 5. Initial Data Sync

Once the containers are running, you need to populate the database with OSRS items.
Execute this command inside the running backend container:

```bash
# Find the backend container name (usually flipping-calculator-backend-1)
docker compose exec backend curl -X POST http://localhost:8000/api/items/sync
```

You should see a success message indicating items have been synced.

## 6. Accessing the Application

Open your browser and navigate to:
`http://YOUR_SERVER_IP:3080` (or whichever port you configured).

## 7. Reverse Proxy (Optional)

If you want to access the app via a domain (e.g., `flips.yourdomain.com`) and HTTPS, use Nginx on your host machine to proxy traffic to the Docker container.

### Install Nginx on Host

```bash
sudo apt install nginx -y
```

### Configure Nginx

Create a new site config: `sudo nano /etc/nginx/sites-available/flipping-calculator`

```nginx
server {
    server_name flips.yourdomain.com;

    location / {
        proxy_pass http://localhost:3080; # Point to the Docker mapped port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable Site & SSL

```bash
sudo ln -s /etc/nginx/sites-available/flipping-calculator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d flips.yourdomain.com
```

## 8. Maintenance

### Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart containers
docker compose up -d --build
```

### Backing Up Database

```bash
docker compose exec db pg_dump -U flipping_user osrs_flipping > backup.sql
```
