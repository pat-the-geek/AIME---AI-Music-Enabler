#!/usr/bin/env bash
set -euo pipefail

# deploy/deploy.sh
# Usage:
#   ./deploy/deploy.sh --host user@host [--port 22] [--key /path/to/key] [--app-dir /opt/aime]
# Assumptions:
# - You have SSH key access to the remote host (recommended).
# - Remote has sudo privileges to install packages and manage systemd.
# - This script will clone the repo (if missing) and run docker compose build/up on the remote.

SSH_OPTS=()
PORT=22
KEY=""
APP_DIR="/opt/aime"
REPO_URL="$(git config --get remote.origin.url || echo '')"
if [ -z "$REPO_URL" ]; then
  echo "Erreur: impossible de déterminer l'URL du dépôt git local. Exécutez depuis la racine du dépôt ou fournissez REPO_URL dans le script."
  exit 1
fi

# secrets copy behaviour: 'auto' (copy if exists), 'force' (fail if missing), 'skip'
COPY_SECRETS="auto"

# caddy install options
INSTALL_CADDY="false"
DOMAIN=""

print_usage(){
  sed -n '1,120p' "$0" | sed -n '1,40p'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --key) KEY="$2"; shift 2;;
    --app-dir) APP_DIR="$2"; shift 2;;
    --install-caddy) INSTALL_CADDY="true"; shift 1;;
    --domain) DOMAIN="$2"; shift 2;;
    --copy-secrets) COPY_SECRETS="force"; shift 1;;
    --skip-secrets) COPY_SECRETS="skip"; shift 1;;
    --help|-h) print_usage; exit 0;;
    *) echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

if [ -z "${HOST:-}" ]; then
  echo "Usage: $0 --host user@host [--port 22] [--key /path/to/key] [--app-dir /opt/aime]"
  exit 1
fi

if [ -n "$KEY" ]; then
  SSH_OPTS+=( -i "$KEY" )
fi
SSH_OPTS+=( -p "$PORT" )

echo "Déploiement vers $HOST (dir: $APP_DIR)"

ssh_cmd(){
  ssh "${SSH_OPTS[@]}" "$HOST" -- "$@"
}

scp_cmd(){
  scp "${SSH_OPTS[@]}" "$1" "$HOST":"$2"
}

# 1) Ensure remote dir and git clone or pull
echo "(1/7) Préparer le répertoire sur la machine distante"
ssh_cmd "sudo mkdir -p '$APP_DIR' && sudo chown \$(whoami):\$(whoami) '$APP_DIR' || true"
ssh_cmd "if [ ! -d '$APP_DIR/.git' ]; then git clone '$REPO_URL' '$APP_DIR'; else cd '$APP_DIR' && git fetch --all && git reset --hard origin/\$(git -C . rev-parse --abbrev-ref HEAD || echo main); fi"

# 2) Ensure Docker + docker-compose plugin available (simple attempt for Debian/Ubuntu systems)
echo "(2/7) Installer Docker si nécessaire (sudo)"
ssh_cmd "if ! command -v docker >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin; sudo systemctl enable --now docker; fi || true"

# 3) Copy secrets (controlled by COPY_SECRETS)
LOCAL_SECRETS_PATH="config/secrets.json"
if [ "$COPY_SECRETS" = "force" ]; then
  echo "(3/7) Forcer la copie des secrets — le fichier local doit exister"
  if [ -f "$LOCAL_SECRETS_PATH" ]; then
    scp_cmd "$LOCAL_SECRETS_PATH" "$APP_DIR/config/secrets.json"
    ssh_cmd "chmod 600 '$APP_DIR/config/secrets.json' || true"
  else
    echo "Fichier $LOCAL_SECRETS_PATH introuvable — annulation." >&2
    exit 1
  fi
elif [ "$COPY_SECRETS" = "skip" ]; then
  echo "(3/7) Skip copy secrets as requested"
else
  # auto mode: copy if present, otherwise skip
  if [ -f "$LOCAL_SECRETS_PATH" ]; then
    echo "(3/7) Copier secrets vers le serveur (auto)"
    scp_cmd "$LOCAL_SECRETS_PATH" "$APP_DIR/config/secrets.json"
    ssh_cmd "chmod 600 '$APP_DIR/config/secrets.json' || true"
  else
    echo "(3/7) Aucun fichier $LOCAL_SECRETS_PATH local trouvé — sautez la copie des secrets"
  fi
fi

# 4) Build images and start compose
echo "(4/7) Build & démarrage docker-compose sur la machine distante"
ssh_cmd "cd '$APP_DIR' && sudo docker compose pull || true && sudo docker compose build --pull && sudo docker compose up -d --remove-orphans"

# 5) Install systemd unit (deploy/aime.service must exist in repository deploy/)
echo "(5/7) Installer l'unité systemd locale si présente"
ssh_cmd "if [ -f '$APP_DIR/deploy/aime.service' ]; then sudo cp '$APP_DIR/deploy/aime.service' /etc/systemd/system/aime.service && sudo systemctl daemon-reload && sudo systemctl enable --now aime.service; else echo 'Pas d\'unité systemd trouvée dans le dépôt (deploy/aime.service)'; fi"

# Optional: install and configure Caddy on the remote host
if [ "$INSTALL_CADDY" = "true" ]; then
  if [ -z "$DOMAIN" ]; then
    echo "--install-caddy requires --domain <your-domain>" >&2
    exit 1
  fi
  echo "(5.5/7) Installer Caddy et déployer Caddyfile pour $DOMAIN"
  ssh_cmd "if ! command -v caddy >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y wget gnupg2 debian-keyring debian-archive-keyring apt-transport-https curl && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list && sudo apt-get update && sudo apt-get install -y caddy; fi"
  if [ -f "deploy/Caddyfile" ]; then
    scp_cmd "deploy/Caddyfile" "/tmp/aime.Caddyfile"
    ssh_cmd "sudo sed -e 's#example.com#${DOMAIN}#g' /tmp/aime.Caddyfile | sudo tee /etc/caddy/Caddyfile > /dev/null && sudo chown root:root /etc/caddy/Caddyfile && sudo systemctl enable --now caddy || true"
  else
    echo "Aucun fichier deploy/Caddyfile local trouvé — skipping Caddyfile install"
  fi
fi

# 6) Optionnel: vérifier santé
echo "(6/7) Tester endpoint santé sur la machine distante (si backend expose /health sur 8000)"
ssh_cmd "if command -v curl >/dev/null 2>&1; then curl -sS http://127.0.0.1:8000/health || true; else echo 'curl non trouvé sur la machine distante'; fi"

# 7) Final
echo "(7/7) Déploiement terminé — vérifiez les logs si nécessaire: ssh $HOST 'sudo docker compose logs -f'"

echo "Terminé. Si vous voulez que je remplace 'example.com' dans le Caddyfile et installe Caddy automatiquement, relancez ce script avec instructions supplémentaires."
