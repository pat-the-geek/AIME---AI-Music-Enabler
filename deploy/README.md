# Déploiement AIME - AI Music Enabler

Ce fichier décrit une procédure simple pour déployer l'application AIME sur une machine distante (serveur Linux, ex. Ubuntu).

PRE-REQUIS
- Machine cible avec accès SSH et privilèges sudo
- Docker et Docker Compose (ou plugin `docker compose`) installés
- Avoir le dépôt AIME sur la machine cible ou y copier les fichiers
- Copier les fichiers sensibles (`config/secrets.json`, `.env`) sur la machine cible (ne pas committer ces fichiers)

1) Installer Docker & Docker Compose (exemple Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
```

2) Cloner le dépôt et positionner les fichiers
```bash
cd /opt
sudo git clone <votre-repo-url> aime
cd /opt/aime
# Copier les secrets depuis votre poste local (SCP)
# scp config/secrets.json user@your-server:/opt/aime/config/secrets.json
sudo chown -R $USER:$USER config data
chmod 600 config/secrets.json
```

3) Variables d'environnement (optionnel)
- Vous pouvez créer un fichier `.env` dans `/opt/aime` avec les variables suivantes :
```
ENVIRONMENT=production
EURIA_API_URL=...
EURIA_BEARER_TOKEN=...
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
LASTFM_API_KEY=...
```

4) Construire et démarrer
```bash
cd /opt/aime
# build (optionnel si vous utilisez images publiques)
docker compose build

# démarrer en arrière-plan
docker compose up -d
```

5) Initialiser la base de données (si nécessaire)
```bash
docker compose run --rm backend python -c "from app.database import init_db; init_db(); print('DB initialized')"
```

6) Vérifier l'état
```bash
docker compose ps
docker compose logs -f backend
curl http://localhost:8000/health
```

7) (Option) Service systemd pour démarrage automatique
- Copier `deploy/aime.service` vers `/etc/systemd/system/aime.service` puis :
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now aime.service
sudo systemctl status aime.service
```

8) Reverse proxy & TLS (exemple Caddy)
- Installez Caddy (https://caddyserver.com/docs/install)
- Copier `deploy/Caddyfile` dans `/etc/caddy/Caddyfile` et remplacer `example.com` par votre domaine
- Redémarrer Caddy : `sudo systemctl restart caddy`

Exemple rapide de firewall (UFW)
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

9) Mise à jour / maintenance
```bash
cd /opt/aime
git pull origin main
docker compose build
docker compose up -d --remove-orphans
```

10) Sauvegardes
- Sauvegarder les volumes `data` et `config` régulièrement :
```bash
docker run --rm -v "$(pwd)/data:/data" -v /tmp:/backup alpine \
  sh -c "cd /data && tar czf /backup/aime-data-$(date +%F).tgz ."
```

Sécurité & conseils
- Ne poussez jamais `config/secrets.json` vers un dépôt public
- Préférez Postgres externe pour production si besoin de réplication
- Utilisez Caddy/Traefik/Nginx pour TLS, domaines et redirection

---
Fichiers fournis dans ce dossier :
- `aime.service` : unit systemd d'exemple
- `Caddyfile` : configuration Caddy exemple
