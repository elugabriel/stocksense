#!/usr/bin/env bash
# Runbook steps 2-3: create the Postgres user/database, password-protect Redis, and write .env
# with freshly generated secrets. Run as root ON THE DROPLET after setup-server.sh:
#   bash /opt/njsmartstock/deploy/configure-server.sh
# Secrets are generated here and written only to .env (mode 600); nothing is printed.
set -euo pipefail

D=njsmartstock.co.uk
APP=/opt/njsmartstock

if [ "$(id -u)" -ne 0 ]; then echo "Run as root on the droplet."; exit 1; fi
if [ -f "$APP/.env" ]; then echo "$APP/.env already exists - not overwriting. Delete it first to regenerate."; exit 1; fi

DBPW=$(openssl rand -hex 16)
REDISPW=$(openssl rand -hex 16)
SECRET=$(python3 -c "import secrets;print(secrets.token_urlsafe(64))")

# Postgres user + database (idempotent)
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='njsmartstock_app'" | grep -q 1; then
  sudo -u postgres psql -c "ALTER USER njsmartstock_app WITH PASSWORD '$DBPW';"
else
  sudo -u postgres psql -c "CREATE USER njsmartstock_app WITH PASSWORD '$DBPW';"
fi
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='njsmartstock'" | grep -q 1; then
  sudo -u postgres psql -c "CREATE DATABASE njsmartstock OWNER njsmartstock_app;"
fi

# Redis: password + make sure it only listens on localhost
CONF=/etc/redis/redis.conf
grep -Eq '^bind 127\.0\.0\.1' "$CONF" || echo "WARNING: redis is not bound to 127.0.0.1 only - check $CONF"
sed -i '/^requirepass /d' "$CONF"
echo "requirepass $REDISPW" >> "$CONF"
systemctl restart redis-server

cat > "$APP/.env" <<ENV
SECRET_KEY=$SECRET
DEBUG=False
ALLOWED_HOSTS=$D,www.$D
CORS_ALLOWED_ORIGINS=https://$D,https://www.$D
DATABASE_URL=postgres://njsmartstock_app:$DBPW@127.0.0.1:5432/njsmartstock
REDIS_URL=redis://:$REDISPW@127.0.0.1:6379/0
AI_ENGINE_URL=http://127.0.0.1:8001
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
SMS_ALERTS_ENABLED=False
ENV
chown njsmartstock:njsmartstock "$APP/.env"
chmod 600 "$APP/.env"

REDISCLI_AUTH="$REDISPW" redis-cli ping
echo "Done: database, Redis and $APP/.env are configured."
