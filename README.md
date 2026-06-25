# Riftbound Library

A lightweight, high-performance web application built to manage a shared Riftbound TCG card library. It tracks physical card inventory, ownership, transaction logs (loans/returns), and automatically syncs daily market prices via the TCGPlayer API.

## Architecture & Tech Stack

* **Backend:** Python 3, FastAPI, Uvicorn
* **Database:** SQLite3 (`tcg.db`)
* **Frontend:** Vanilla HTML/JS/CSS (Served natively by FastAPI)
* **Reverse Proxy / SSL:** Caddy Server
* **Task Scheduling:** Systemd Timers (Daily Price Sync)
* **Hosting:** Google Cloud Platform (Ubuntu VM)

---

## Directory Structure

The application is designed to run from the home directory (`/home/connormunger/tcg-app`).

```text
tcg-app/
├── app/
│   ├── main.py                # FastAPI application & API endpoints
│   └── static/
│       └── index.html         # Frontend interface
├── data/
│   └── tcgapi_key.txt         # Secret API key (Ignored by Git)
├── sync_prices.py             # Script to fetch daily market prices
├── tcg.db                     # Live SQLite database (Ignored by Git)
├── venv/                      # Python virtual environment (Ignored by Git)
├── .gitignore
└── README.md

```

---

## Server Setup & Replication Guide

If you need to deploy this project on a brand-new Ubuntu VM, follow these steps.

### 1. Initial System Setup

Update the server and install the required system packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-venv sqlite3 git debian-keyring debian-archive-keyring apt-transport-https -y

```

### 2. Clone the Repository

Generate an SSH key (`ssh-keygen -t ed25519`), add it to GitHub, and clone the code:

```bash
git clone git@github.com:YOUR_GITHUB_USERNAME/riftbound-library.git tcg-app
cd tcg-app

```

### 3. Setup the Python Environment

Create the virtual environment and install the FastAPI dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn

```

### 4. Restore Data & API Keys

Because sensitive data is blocked by `.gitignore`, you must manually move two files to the new server:

1. Upload your backup of `tcg.db` into the `~/tcg-app/` folder.
2. Recreate the API key file:
```bash
mkdir -p ~/tcg-app/data
nano ~/tcg-app/data/tcgapi_key.txt

```


*(Paste your TCG API key here and save).*

---

## Background Services (Systemd)

The application relies on `systemd` to keep the web server online and to schedule the daily price updates.

### 1. The FastAPI Web Server

Create the service file:

```bash
sudo nano /etc/systemd/system/tcgapp.service

```

**Contents:**

```ini
[Unit]
Description=FastAPI TCG Inventory App
After=network.target

[Service]
User=connormunger
WorkingDirectory=/home/connormunger/tcg-app
ExecStart=/home/connormunger/tcg-app/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

```

Enable and start the server:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tcgapp.service

```

### 2. The Daily Price Sync Timer
Pulls market pricing updates at 01:00 UTC every day.
- Service (`/etc/systemd/system/tcg-prices.service`):

```ini
[Unit]
Description=Riftbound Price Sync (TCG API)
After=network.target

[Service]
Type=oneshot
User=connormunger
WorkingDirectory=/home/connormunger/tcg-app
ExecStart=/home/connormunger/tcg-app/venv/bin/python /home/connormunger/tcg-app/sync_prices.py

```
- Timer (`/etc/systemd/system/tcg-prices.timer`):

```ini
[Unit]
Description=Run Riftbound Price Sync Daily

[Timer]
OnCalendar=*-*-* 01:00:00
Persistent=true

[Install]
WantedBy=timers.target

```
### 3. The Daily Database Backup Timer
Safely clones, compresses, and pushes the live SQLite database file to Google Cloud Storage at 03:00 UTC daily.
- Service (`/etc/systemd/system/tcg-backup.service`):

```ini
[Unit]
Description=Riftbound Database Backup to GCS
After=network.target

[Service]
Type=oneshot
User=connormunger
WorkingDirectory=/home/connormunger/tcg-app
ExecStart=/home/connormunger/tcg-app/backup_db.sh

```
- Timer (`/etc/systemd/system/tcg-prices.timer`):

```ini
[Unit]
Description=Run Riftbound Database Backup Daily

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target

```


Enable timers using:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tcg-prices.timer
sudo systemctl enable --now tcg-backup.timer

```

---

## Web Server & Domain Setup (Caddy)

Caddy acts as a reverse proxy, taking standard web traffic from your domain name, securing it with a free Let's Encrypt SSL certificate, and routing it to the internal FastAPI server.

1. **Install Caddy** (Refer to the official Caddy docs for the latest Ubuntu installation commands).
2. **Configure the Domain:**
```bash
sudo nano /etc/caddy/Caddyfile

```


3. **Contents:**
```caddy
connormunger.com, [www.connormunger.com](https://www.connormunger.com) {
    reverse_proxy 127.0.0.1:8000
}

```


4. **Reload Caddy:**
```bash
sudo systemctl reload caddy

```



---

## Development Workflow

To make changes to the app, follow this loop:

1. **Write code locally** and push it to GitHub (`git push`).
2. **Pull changes** to the VM:
```bash
cd ~/tcg-app
git pull

```


3. **Restart the service** to apply Python backend changes:
```bash
sudo systemctl restart tcgapp

```


*(Note: Changes made strictly to `index.html` do not require a service restart, just a browser refresh).*

### Useful Maintenance Commands

- View Web logs: `sudo journalctl -u tcgapp -n 50 --no-pager`
- View Price Sync logs: `sudo journalctl -u tcg-prices.service -n 50 --no-pager`
- View Backup logs: `sudo journalctl -u tcg-backup.service -n 50 --no-pager`
- Force Manual Price Sync: `sudo systemctl start tcg-prices.service`
- Force Manual Database Backup: `sudo systemctl start tcg-backup.service`
- Interact with Database: `sqlite3 ~/tcg-app/tcg.db`

```

```
