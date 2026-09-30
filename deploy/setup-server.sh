#!/usr/bin/env bash
# One-shot base provisioning for a fresh Ubuntu 24.04 droplet. Run as root:
#   bash /opt/njsmartstock/deploy/setup-server.sh
# Afterwards follow deploy/README.md (database, .env, services, certbot).
set -euo pipefail

DOMAIN=njsmartstock.co.uk
APP=/opt/njsmartstock
REPO=https://github.com/elugabriel/stocksense.git

# Swap: a 2 GB box runs Postgres, Redis, Daphne, Celery and the AI engine together
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y install postgresql redis-server nginx certbot \
  python3-certbot-nginx python3-venv python3-dev build-essential libpq-dev git ufw

# Firewall: SSH + HTTP/HTTPS only
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# App user + code
id njsmartstock &>/dev/null || useradd --system --create-home --shell /bin/bash njsmartstock
[ -d "$APP/.git" ] || git clone "$REPO" "$APP"
chown -R njsmartstock:njsmartstock "$APP"

# Python environments
sudo -u njsmartstock python3 -m venv "$APP/venv"
sudo -u njsmartstock "$APP/venv/bin/pip" install -r "$APP/requirements.txt"
sudo -u njsmartstock python3 -m venv "$APP/ai-engine/venv"
sudo -u njsmartstock "$APP/ai-engine/venv/bin/pip" install -r "$APP/ai-engine/requirements.txt"

# systemd units + nginx site
cp "$APP"/deploy/njsmartstock-*.service /etc/systemd/system/
systemctl daemon-reload
cp "$APP/deploy/nginx-njsmartstock.conf" /etc/nginx/sites-available/njsmartstock
ln -sf /etc/nginx/sites-available/njsmartstock /etc/nginx/sites-enabled/njsmartstock
rm -f /etc/nginx/sites-enabled/default
# nginx (www-data) must be able to traverse into the app dir for frontend + static files
chmod o+x /opt "$APP"
nginx -t && systemctl reload nginx

echo
echo "Base install done for $DOMAIN. Continue with deploy/README.md from step 2 (database)."
