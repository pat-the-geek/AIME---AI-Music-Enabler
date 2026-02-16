# Déploiement — AIME (AI Music Enabler)

Ce document fournit une checklist concise et les commandes pour déployer AIME sur une machine distante en production légère (Docker + docker compose, optionnellement Caddy).

**Fichiers importants**
- `deploy/deploy.sh` — script d'automatisation SSH (clone, build, up, install systemd, option Caddy).
- `deploy/aime.service` — unité systemd (utilise `docker compose`).
- `deploy/Caddyfile` — exemple Caddyfile (remplacer `example.com`).
- `config/secrets.json` — secrets à copier sur le serveur (permissions 600).

**Prérequis (côté local)**
- Clé SSH configurée et accès `user@host` au serveur.
- Le dépôt git doit avoir une `remote.origin` renseignée.
- Avoir le fichier `config/secrets.json` local si vous souhaitez le copier.

**Prérequis (côté distant)**
- Système Debian/Ubuntu recommandé (les commandes d'installation sont pour Debian/Ubuntu).
- Accès `sudo` pour l'utilisateur distant pour installer Docker/Caddy et gérer systemd.
- Ports : 80/443 pour Caddy (optionnel), 8000 (backend) et 80 (frontend) en interne.

---

## Commandes d'usage rapide

- Vérifier la syntaxe du script et afficher l'aide :
```bash
bash -n deploy/deploy.sh
./deploy/deploy.sh --help
```

- Déploiement simple (auto-copy secrets si présent) :
```bash
./deploy/deploy.sh --host user@host --key ~/.ssh/id_rsa
```

- Forcer la copie des secrets et installer Caddy pour `example.com` :
```bash
./deploy/deploy.sh \
  --host user@host --key ~/.ssh/id_rsa \
  --app-dir /opt/aime --copy-secrets --install-caddy --domain example.com
```

- Si vous ne voulez PAS copier les secrets depuis la machine locale :
```bash
./deploy/deploy.sh --host user@host --skip-secrets
```

---

## Checklist détaillée (manuelle)

1. Préparer le serveur
   - Ajouter votre clé SSH dans `~/.ssh/authorized_keys` de l'utilisateur distant.
   - Ouvrir les ports 22 (SSH), 80 et 443 si vous installez Caddy.

2. Copier `config/secrets.json` (si non utilisé via `--copy-secrets`):
```bash
scp -i ~/.ssh/id_rsa config/secrets.json user@host:/tmp/secrets.json
ssh -i ~/.ssh/id_rsa user@host 'sudo mkdir -p /opt/aime/config && sudo mv /tmp/secrets.json /opt/aime/config/secrets.json && sudo chown -R $(whoami):$(whoami) /opt/aime && sudo chmod 600 /opt/aime/config/secrets.json'
```

3. Installer Docker sur le serveur (si besoin)
```bash
ssh user@host 'sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin && sudo systemctl enable --now docker'
```

4. Cloner et lancer (manuel)
```bash
ssh user@host 'sudo mkdir -p /opt/aime && sudo chown $(whoami):$(whoami) /opt/aime'
ssh user@host 'git clone <repo-url> /opt/aime || (cd /opt/aime && git fetch --all && git reset --hard origin/main)'
ssh user@host 'cd /opt/aime && sudo docker compose build --pull && sudo docker compose up -d --remove-orphans'
```

5. Installer l'unité systemd (optionnel)
```bash
ssh user@host 'sudo cp /opt/aime/deploy/aime.service /etc/systemd/system/aime.service && sudo systemctl daemon-reload && sudo systemctl enable --now aime.service'
```

6. Installer Caddy (optionnel)
- Remplacer `example.com` dans `deploy/Caddyfile` par votre domaine et vérifier DNS pointant sur l'IP publique du serveur.
- Installer via apt (Debian/Ubuntu) et activer :
```bash
ssh user@host 'sudo apt-get update && sudo apt-get install -y caddy'
ssh user@host 'sudo cp /opt/aime/deploy/Caddyfile /etc/caddy/Caddyfile && sudo systemctl enable --now caddy'
```

7. Vérifier l'état / health
```bash
ssh user@host 'curl -sS http://127.0.0.1:8000/health'
# ou depuis votre réseau si ports exposés
curl -sS http://<server-ip>:8000/health
```

8. Logs & debug
```bash
ssh user@host 'sudo docker compose logs -f'
ssh user@host 'sudo journalctl -u aime.service -f'
```

---

## Rollback rapide
- Pour arrêter et restaurer l'état antérieur :
```bash
ssh user@host 'cd /opt/aime && sudo docker compose down && sudo git reset --hard origin/main && sudo docker compose up -d'
```

---

## Sécurité & bonnes pratiques
- Ne stockez pas `config/secrets.json` dans un dépôt public.
- Donnez des permissions `600` au fichier de secrets sur le serveur.
- Utilisez un utilisateur restreint pour exécuter Docker et évitez d'utiliser `root` pour vos applications applicatives.
- Configurez un pare-feu (ufw) pour limiter l'accès aux ports nécessaires.

---

## Remarques
- Le script `deploy/deploy.sh` tente d'être générique pour Debian/Ubuntu ; adaptez les étapes d'installation si vous utilisez une autre distribution.
- Si vous souhaitez que j'exécute le déploiement vers un hôte cible (avec SSH key), fournissez `user@host` et je lancerai le script.


