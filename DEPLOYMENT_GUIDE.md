# Production Deployment Guide: https://kiafloor.sabtom.com/

This guide outlines the complete step-by-step setup to deploy the KIA Floor Process Validation application live at **https://kiafloor.sabtom.com/**.

---

## 1. Summary of Changes Applied to Codebase

- **Host & Domain Whitelisting**: Added `kiafloor.sabtom.com` and `.sabtom.com` to `ALLOWED_HOSTS` in [settings.py](file:///d:/projects/kia/demo/config/settings.py).
- **HTTPS & CSRF Security**: Configured `CSRF_TRUSTED_ORIGINS = ['https://kiafloor.sabtom.com']` and enabled reverse proxy SSL headers (`SECURE_PROXY_SSL_HEADER`).
- **Static File Handling**: Configured `STATIC_ROOT` and generated bundled static assets into `staticfiles/`.
- **Environment Overrides**: `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` are dynamically configurable via server environment variables.

---

## 2. Quick Deployment Option A: Bare Metal / Linux Server (Ubuntu/Debian)

### Step 1: Transfer Code to Server
```bash
git clone <your-repo-url> /var/www/kiafloor
# OR rsync / upload project files to /var/www/kiafloor
cd /var/www/kiafloor
```

### Step 2: Install Virtual environment & Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

### Step 3: Configure Systemd Service
Copy the included service file:
```bash
sudo cp deploy/kiafloor.service /etc/systemd/system/kiafloor.service
sudo systemctl daemon-reload
sudo systemctl enable --now kiafloor
```

### Step 4: Configure Nginx & SSL Certificate
Copy the pre-built Nginx configuration:
```bash
sudo cp deploy/nginx_kiafloor.conf /etc/nginx/sites-available/kiafloor.sabtom.com
sudo ln -s /etc/nginx/sites-available/kiafloor.sabtom.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Obtain free SSL certificate via Certbot:
```bash
sudo certbot --nginx -d kiafloor.sabtom.com
```

---

## 3. Quick Deployment Option B: Docker Container

If using Docker / Docker Compose / CapRover / Portainer:

```bash
docker compose up -d --build
```

Nginx / Cloudflare / Reverse proxy can route `https://kiafloor.sabtom.com` to port `8000`.

---

## 4. Verification Checklist

1. Open **https://kiafloor.sabtom.com/** in your web browser.
2. Log in with sample operator or manager credentials.
3. Test barcode generation and dynamic process validation scenarios.
4. Verify form POST submissions complete without 403 CSRF errors.
