# Frontend Setup Guide

This guide covers setting up the **Flipping Calculator Frontend**. For a dedicated server (Mini PC/Raspberry Pi), we recommend **building** the application and serving it statically, rather than running the development server.

## 📋 Prerequisites

*   **Node.js:** v18.0.0 or higher
*   **npm:** v9.0.0 or higher

### Install Node.js (Ubuntu/Debian)
```bash
# Using NodeSource for newer versions
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## 🚀 Installation

Navigate to the frontend directory:
```bash
cd flipping-calculator-frontend
```

Install dependencies:
```bash
npm install
```

## 🏃‍♂️ Development Mode
For coding and testing changes:

```bash
npm run dev
```
*   **URL:** `http://localhost:3000`
*   **API Proxy:** Configured in `vite.config.js` to point to `http://localhost:8000`

## 🏭 Production Deployment (Recommended for Server)

For your Mini PC, you should build the app and serve the static files. This uses negligible CPU/RAM compared to `npm run dev`.

### 1. Build the App
```bash
npm run build
```
This creates a `dist/` directory with optimized HTML/CSS/JS files.

### 2. Serving the App

#### Option A: Simple Serve (Easiest)
Use a lightweight static server like `serve`.

```bash
sudo npm install -g serve
serve -s dist -l 3000
```

#### Option B: Nginx (Best Performance/Security)
Install Nginx:
```bash
sudo apt install nginx
```

Create a config: `sudo nano /etc/nginx/sites-available/osrs-flip`

```nginx
server {
    listen 80;
    server_name _;  # Or your server's IP/domain

    root /path/to/flipping-calculator/flipping-calculator-frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to Backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable it:
```bash
sudo ln -s /etc/nginx/sites-available/osrs-flip /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

## ⚙️ Configuration

### API Connection
The frontend connects to the backend API.
*   **Dev Mode:** Uses Vite proxy (`vite.config.js`) to `http://localhost:8000`.
*   **Production:** The code assumes the API is at the same domain/port under `/api` (if using Nginx proxy) OR requires you to set the `VITE_API_URL` environment variable at build time.

To hardcode the API URL for a build:
```bash
VITE_API_URL="http://192.168.1.100:8000/api" npm run build
```

## 🧹 Maintenance

*   **Update Dependencies:**
    ```bash
    npm update
    ```
*   **Clean Install:**
    If things break, delete `node_modules` and `package-lock.json` and reinstall.
    ```bash
    rm -rf node_modules package-lock.json
    npm install
    ```
