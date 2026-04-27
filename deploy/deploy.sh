#!/usr/bin/env bash
# =============================================================================
# gym-jams-ai-backend :: deploy.sh
#
# One-shot, idempotent deploy macro for an Amazon Linux 2023 EC2 instance.
# Run this from your LOCAL machine (Git Bash / WSL / macOS / Linux).
# Re-run any time you want to ship a code change — it's safe to re-execute.
#
# Usage:
#   EC2_HOST=ec2-1-2-3-4.ap-northeast-1.compute.amazonaws.com \
#   PEM_PATH=~/keys/gym-jams.pem \
#   bash deploy/deploy.sh
#
# Optional env overrides:
#   REMOTE_USER  (default: ec2-user)
#   APP_DIR      (default: /home/ec2-user/gym-jams-ai-backend)
#   ENV_FILE     (default: ./.env)
# =============================================================================

set -euo pipefail

# ---- Config -----------------------------------------------------------------
: "${EC2_HOST:?EC2_HOST is required, e.g. ec2-1-2-3-4.ap-northeast-1.compute.amazonaws.com}"
: "${PEM_PATH:?PEM_PATH is required, e.g. ~/keys/gym-jams.pem}"
REMOTE_USER="${REMOTE_USER:-ec2-user}"
APP_DIR="${APP_DIR:-/home/ec2-user/gym-jams-ai-backend}"
ENV_FILE="${ENV_FILE:-./.env}"

LOG_FILE="deploy.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SSH_OPTS="-i $PEM_PATH -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30"
SSH="ssh $SSH_OPTS $REMOTE_USER@$EC2_HOST"
SCP="scp $SSH_OPTS"

# Pretty-print phase headers; everything else echoed via `set -x`.
banner() {
    echo ""
    echo "========================================================================"
    echo "==  $*"
    echo "==  $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    echo "========================================================================"
}

# Mirror all output to a log file.
exec > >(tee -a "$LOG_FILE") 2>&1

banner "PHASE 0  Preflight"
set -x
[[ -f "$PEM_PATH" ]] || { echo "PEM file not found at $PEM_PATH" >&2; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo ".env file not found at $ENV_FILE — copy .env.example, fill it in, retry." >&2; exit 1; }
# Warn (not fail) on loose pem perms — Windows filesystems can't always chmod.
PEM_PERMS="$(stat -c '%a' "$PEM_PATH" 2>/dev/null || stat -f '%A' "$PEM_PATH" 2>/dev/null || echo '?')"
echo "PEM perms: $PEM_PERMS (should be 400 on unix-like FS)"
$SSH "echo 'SSH OK on '\$(hostname); uname -a"
set +x

banner "PHASE 1  Sync source code"
$SSH "mkdir -p $APP_DIR"

if command -v rsync >/dev/null 2>&1; then
    echo "Using rsync (faster, incremental)"
    set -x
    rsync -avz --delete \
        --exclude '.git/' \
        --exclude '.venv/' \
        --exclude '__pycache__/' \
        --exclude '*.pyc' \
        --exclude 'results/' \
        --exclude 'deploy.log' \
        --exclude '.env' \
        --exclude '*.pem' \
        --exclude 'node_modules/' \
        -e "ssh $SSH_OPTS" \
        "$PROJECT_ROOT/" "$REMOTE_USER@$EC2_HOST:$APP_DIR/"
    set +x
else
    echo "rsync not found — falling back to tar-over-ssh (slower but no extra deps)"
    set -x
    # Stream a tarball of the project up through SSH. The remote untars into
    # $APP_DIR. We don't --delete remote files in this mode (acceptable for MVP);
    # to wipe stale files do: ssh ... 'rm -rf $APP_DIR/*' before deploy.
    tar -C "$PROJECT_ROOT" \
        --exclude='./.git' \
        --exclude='./.venv' \
        --exclude='./__pycache__' \
        --exclude='*.pyc' \
        --exclude='./results' \
        --exclude='./deploy.log' \
        --exclude='./.env' \
        --exclude='*.pem' \
        --exclude='./node_modules' \
        -czf - . \
        | $SSH "tar -xzf - -C $APP_DIR"
    set +x
fi

banner "PHASE 2  Copy .env"
set -x
$SCP "$ENV_FILE" "$REMOTE_USER@$EC2_HOST:$APP_DIR/.env"
# Force DB connection vars to match the Docker MySQL container set up below.
# This protects against placeholder values in your local .env.
$SSH "sed -i \
    -e 's|^DB_HOST=.*|DB_HOST=127.0.0.1|' \
    -e 's|^DB_PORT=.*|DB_PORT=3306|' \
    -e 's|^DB_USER=.*|DB_USER=root|' \
    -e 's|^DB_PASSWORD=.*|DB_PASSWORD=root|' \
    -e 's|^DB_NAME=.*|DB_NAME=gym_jams_db|' \
    $APP_DIR/.env"
set +x

banner "PHASE 3  Provision server (system packages, docker, mysql, venv, systemd, nginx)"
# Send a heredoc'd remote script. `bash -s` reads from stdin so the env vars we
# inline at the top are available to it.
$SSH "APP_DIR=$APP_DIR SKIP_DB_INIT=${SKIP_DB_INIT:-0} bash -s" <<'REMOTE_SCRIPT'
set -euxo pipefail

# ---- 3a. System packages -------------------------------------------------
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip git nginx docker rsync gcc python3.11-devel

# ---- 3b. Services --------------------------------------------------------
sudo systemctl enable --now docker
sudo systemctl enable --now nginx
# Add user to docker group (takes effect next login; we use sudo for now).
sudo usermod -aG docker ec2-user || true

# ---- 3c. MySQL container (idempotent) ------------------------------------
if sudo docker ps -a --format '{{.Names}}' | grep -qx 'gym-jams-db'; then
    echo "MySQL container exists — ensuring it is running"
    sudo docker start gym-jams-db || true
else
    echo "Creating MySQL container"
    sudo docker run -d \
        --name gym-jams-db \
        --restart unless-stopped \
        -e MYSQL_ROOT_PASSWORD=root \
        -e MYSQL_ROOT_HOST=% \
        -e MYSQL_DATABASE=gym_jams_db \
        -p 3306:3306 \
        mysql:8.0
fi

# Wait for MySQL to accept connections (up to ~60s).
echo "Waiting for MySQL to be ready..."
for i in $(seq 1 30); do
    if sudo docker exec gym-jams-db mysqladmin ping -uroot -proot --silent >/dev/null 2>&1; then
        echo "MySQL is ready after ${i} attempts"
        break
    fi
    sleep 2
done

# Ensure root can connect from the Docker bridge gateway (host -> container).
# Safe to re-run; CREATE USER IF NOT EXISTS + GRANT are idempotent. Needed
# because pre-existing containers created without MYSQL_ROOT_HOST=% won't have
# root@% — and we connect from the host, which appears as 172.17.0.1 to MySQL.
echo "Ensuring root@% access for host connections..."
sudo docker exec gym-jams-db mysql -uroot -proot -e "
    CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'root';
    GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
    ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'root';
    FLUSH PRIVILEGES;
"

# ---- 3d. Python venv + deps ---------------------------------------------
cd "$APP_DIR"
if [[ ! -d .venv ]]; then
    python3.11 -m venv .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# ---- 3e. DB schema -------------------------------------------------------
# initialize_sql_tables.py drops + recreates tables; idempotent. On first deploy
# this populates the schema. On redeploys, set SKIP_DB_INIT=1 to keep data.
if [[ "${SKIP_DB_INIT:-0}" != "1" ]]; then
    set +e
    .venv/bin/python scripts/utils/initialize_sql_tables.py
    DB_RC=$?
    set -e
    if [[ $DB_RC -ne 0 ]]; then
        echo "WARN: initialize_sql_tables.py exited $DB_RC — continuing (table may already be in desired state)"
    fi
fi

# ---- 3f. systemd unit ----------------------------------------------------
sudo cp "$APP_DIR/deploy/gym-jams.service" /etc/systemd/system/gym-jams.service
sudo systemctl daemon-reload
sudo systemctl enable gym-jams
sudo systemctl restart gym-jams

# ---- 3g. nginx reverse proxy --------------------------------------------
sudo cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/conf.d/gym-jams.conf
# AL2023's stock /etc/nginx/nginx.conf ships a default `server { listen 80
# default_server; server_name _; ... }` block that collides with ours. Strip
# its entire server block once; idempotent because we leave a marker.
if ! grep -q '# gym-jams: default server stripped' /etc/nginx/nginx.conf; then
    sudo python3 - <<'PY'
import re, pathlib
p = pathlib.Path("/etc/nginx/nginx.conf")
src = p.read_text()
# Remove the first server { ... } block inside http { ... }.
new = re.sub(r"\n\s*server\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\n", "\n", src, count=1)
new = "# gym-jams: default server stripped\n" + new
p.write_text(new)
PY
fi
sudo nginx -t
sudo systemctl restart nginx

echo "Provision phase complete."
REMOTE_SCRIPT

banner "PHASE 4  Smoke test"
set -x
sleep 3
curl -fsS "http://$EC2_HOST/health" && echo
curl -fsS "http://$EC2_HOST/" && echo
set +x

banner "DONE  Service is live at http://$EC2_HOST"
echo "Logs saved to: $LOG_FILE"
echo ""
echo "Next steps:"
echo "  - Tail service logs:   ssh -i $PEM_PATH $REMOTE_USER@$EC2_HOST 'sudo journalctl -u gym-jams -f'"
echo "  - Check status:        ssh -i $PEM_PATH $REMOTE_USER@$EC2_HOST 'sudo systemctl status gym-jams'"
echo "  - Redeploy code only:  SKIP_DB_INIT=1 EC2_HOST=$EC2_HOST PEM_PATH=$PEM_PATH bash deploy/deploy.sh"
