# Deploying NJSmartStock (single DigitalOcean droplet)

Domain: `njsmartstock.co.uk`. Droplet: Ubuntu 24.04, 2 GB RAM, London (LON1).
Prerequisite: GoDaddy DNS has `A @` pointing at the droplet IP and `www` CNAME to `njsmartstock.co.uk.`.

## 1. Provision
SSH in as root:
```bash
apt-get update && apt-get -y install git
git clone https://github.com/elugabriel/stocksense.git /opt/njsmartstock
bash /opt/njsmartstock/deploy/setup-server.sh
```

## 2. Database and Redis
```bash
sudo -u postgres psql -c "CREATE USER njsmartstock_app WITH PASSWORD 'CHOOSE_A_STRONG_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE njsmartstock OWNER njsmartstock_app;"
```
In `/etc/redis/redis.conf` confirm `bind 127.0.0.1` and set `requirepass CHOOSE_ANOTHER`, then
`systemctl restart redis-server`.

## 3. Config
```bash
cd /opt/njsmartstock
sudo -u njsmartstock cp .env.production.example .env
sudo -u njsmartstock nano .env
```
Fill in `SECRET_KEY`, the two passwords (URL-encode special characters), and set:
```
ALLOWED_HOSTS=njsmartstock.co.uk,www.njsmartstock.co.uk
CORS_ALLOWED_ORIGINS=https://njsmartstock.co.uk,https://www.njsmartstock.co.uk
```

## 4. Load data
Option A, fresh database:
```bash
sudo -u njsmartstock bash -c 'cd /opt/njsmartstock && export DJANGO_SETTINGS_MODULE=stocksense.settings.prod \
 && venv/bin/python manage.py migrate && venv/bin/python manage.py setup_groups \
 && venv/bin/python manage.py createsuperuser'
```
Option B, restore the clean dump (from your PC: `scp njsmartstock_clean.dump root@DROPLET_IP:/tmp/`):
```bash
pg_restore --no-owner --no-acl -d "postgres://njsmartstock_app:PASSWORD@127.0.0.1:5432/njsmartstock" /tmp/njsmartstock_clean.dump
rm /tmp/njsmartstock_clean.dump
```
Then, either way:
```bash
sudo -u njsmartstock bash -c 'cd /opt/njsmartstock && export DJANGO_SETTINGS_MODULE=stocksense.settings.prod \
 && venv/bin/python manage.py migrate && venv/bin/python manage.py collectstatic --no-input'
```

## 5. Start services
```bash
systemctl enable --now njsmartstock-daphne njsmartstock-celery njsmartstock-celerybeat njsmartstock-ai-engine
systemctl status njsmartstock-daphne --no-pager
```

## 6. HTTPS
DNS must resolve first (`nslookup njsmartstock.co.uk` shows the droplet IP):
```bash
certbot --nginx -d njsmartstock.co.uk -d www.njsmartstock.co.uk
```
Certificates renew automatically.

## 7. Check
Open https://njsmartstock.co.uk, sign in, and change the admin password.
Logs: `journalctl -u njsmartstock-daphne -f` and `/var/log/nginx/error.log`.

## Updating later
```bash
cd /opt/njsmartstock && sudo -u njsmartstock git pull
sudo -u njsmartstock venv/bin/pip install -r requirements.txt
sudo -u njsmartstock env DJANGO_SETTINGS_MODULE=stocksense.settings.prod venv/bin/python manage.py migrate
sudo -u njsmartstock env DJANGO_SETTINGS_MODULE=stocksense.settings.prod venv/bin/python manage.py collectstatic --no-input
systemctl restart njsmartstock-daphne njsmartstock-celery njsmartstock-celerybeat njsmartstock-ai-engine
```
