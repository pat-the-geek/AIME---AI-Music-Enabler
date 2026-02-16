# Release — Guide Pratique pour AIME

Ce guide couvre le cycle complet de release : développement → tests → build → déploiement → rollback si besoin.

## 📋 Checklist Pre-Release

Avant de tagger une version :

- [ ] Tous les commits sont pushés sur `origin`.
- [ ] Tests locaux passent (`npm test` frontend, `pytest` backend si présent).
- [ ] Images Docker builent sans erreur localement : `docker compose build --no-cache`.
- [ ] Containers démarrent et l'endpoint `/health` répond bien.
- [ ] `config/secrets.json` n'est PAS dans le commit.
- [ ] Version mise à jour dans `README.md` (ex. v4.7.1).

## 🏷️ Tagging & Build (Local)

### 1. Déterminer le numéro de version

Utilisez [Semantic Versioning](https://semver.org/) : `MAJOR.MINOR.PATCH`
- `MAJOR` : changements incompatibles (breaking changes)
- `MINOR` : nouvelles fonctionnalités (rétro-compatibles)
- `PATCH` : corrections de bugs

Exemple : v4.7.1 → v4.8.0 (nouvelle feature) ou v4.7.2 (bugfix).

### 2. Créer un tag git local

```bash
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
VERSION="v4.8.0"  # Remplacer par votre version
git tag -a "$VERSION" -m "Release $VERSION"
git push origin "$VERSION"
```

### 3. Builder les images avec le tag

```bash
VERSION="v4.8.0"
docker compose build --no-cache

# Tagger les images (utiliser le tag de commit ou la branche actuelle)
docker tag aime-backend:latest pat-the-geek/aime-backend:$VERSION
docker tag aime-frontend:latest pat-the-geek/aime-frontend:$VERSION

# Optionnel : garder 'latest' à jour
docker tag aime-backend:latest pat-the-geek/aime-backend:latest
docker tag aime-frontend:latest pat-the-geek/aime-frontend:latest
```

**⚠️ Important :** Remplacer `pat-the-geek` par votre Docker Hub username (ou registry préféré).

### 4. Pousser les images vers un registre (Docker Hub recommandé)

Si vous n'avez pas encore de compte Docker Hub :
- Créer compte sur [hub.docker.com](https://hub.docker.com/).
- Se connecter localement : `docker login`.

```bash
VERSION="v4.8.0"
docker push pat-the-geek/aime-backend:$VERSION
docker push pat-the-geek/aime-frontend:$VERSION
docker push pat-the-geek/aime-backend:latest
docker push pat-the-geek/aime-frontend:latest
```

Vérifier les images sur : https://hub.docker.com/r/pat-the-geek/

## 🚀 Déploiement en Production

### Option 1 : Déployer en construisant sur le serveur (simple)

Votre `deploy/deploy.sh` clone le dépôt et build sur place — idéal pour petits déploiements.

```bash
./deploy/deploy.sh --host user@host --key ~/.ssh/id_rsa --app-dir /opt/aime --copy-secrets
```

### Option 2 : Déployer depuis des images taggées (recommandé pour prod)

Créer une version `docker-compose.prod.yml` qui référence vos images taggées :

```yaml
services:
  backend:
    image: pat-the-geek/aime-backend:v4.8.0  # Tag exact, pas 'latest'
    # ... reste de la config

  frontend:
    image: pat-the-geek/aime-frontend:v4.8.0
    # ... reste de la config
```

Puis sur le serveur :

```bash
ssh user@host
cd /opt/aime
git pull origin main  # Pour récupérer docker-compose.prod.yml
export VERSION=v4.8.0
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans
curl http://127.0.0.1:8000/health  # Vérifier la santé
```

## ✅ Vérification Post-Deploy

Après déploiement, vérifier immédiatement :

```bash
# Depuis votre machine locale
curl -sS http://<server-ip>:8000/health | jq .

# Ou via SSH
ssh user@host 'sudo docker compose logs -f backend' &
ssh user@host 'curl -sS http://127.0.0.1:8000/health'

# Vérifier les conteneurs
ssh user@host 'sudo docker compose ps'
```

Points à checker :
- Status HTTP 200 sur `/health`.
- Pas d'erreurs dans les logs (exception, crash).
- Frontend accessible sur le port 80.
- Scheduler ou autres services critiques tournent (si présents dans logs).

## 🔄 Rollback Rapide

Si quelque chose va mal après déploiement :

### Rollback avec un tag antérieur

1. Retrouver la version précédente :
```bash
git tag | grep -E '^v[0-9]' | sort -V | tail -5
```

2. Redéployer avec l'ancienne version :
```bash
OLD_VERSION="v4.7.2"
./deploy/deploy.sh --host user@host --key ~/.ssh/id_rsa --app-dir /opt/aime
# (la version depuis main, ou modifiez docker-compose.yml)
```

### Rollback via docker compose (sans rebuild)

```bash
ssh user@host
cd /opt/aime
# Retrouver l'image antérieure (si vous avez poussé avec 'latest')
docker compose -f docker-compose.prod.yml down
docker tag pat-the-geek/aime-backend:latest-backup pat-the-geek/aime-backend:latest
docker compose -f docker-compose.prod.yml up -d --remove-orphans
```

Ou simplement : pull l'image antérieure depuis le registre, tagger et redémarrer.

## 📝 Exemple Complet (Étape par Étape)

Scénario : vous avez développé une feature en branche `feature/new-collection-type`, elle est testée, et prête pour production (v4.8.0).

```bash
# 1. Merger la branche
git checkout main
git pull origin main
git merge --ff-only feature/new-collection-type
git push origin main

# 2. Tagger
VERSION="v4.8.0"
git tag -a "$VERSION" -m "Release $VERSION: Add new collection type"
git push origin "$VERSION"

# 3. Builder localement et tagger images
docker compose build --no-cache
docker tag aime-backend:latest pat-the-geek/aime-backend:$VERSION
docker tag aime-frontend:latest pat-the-geek/aime-frontend:$VERSION
docker tag aime-backend:latest pat-the-geek/aime-backend:latest
docker tag aime-frontend:latest pat-the-geek/aime-frontend:latest

# 4. Tester localement
docker compose down
docker compose up -d
sleep 5
curl -sS http://127.0.0.1:8000/health | jq .
docker compose logs backend

# 5. Pousser vers registry
docker login
docker push pat-the-geek/aime-backend:$VERSION
docker push pat-the-geek/aime-frontend:$VERSION
docker push pat-the-geek/aime-backend:latest
docker push pat-the-geek/aime-frontend:latest

# 6. Déployer sur prod
./deploy/deploy.sh --host user@prod-server --key ~/.ssh/id_rsa --app-dir /opt/aime --copy-secrets

# 7. Vérifier
ssh user@prod-server 'curl -sS http://127.0.0.1:8000/health'
ssh user@prod-server 'sudo docker compose logs -f backend'

# 8. Si OK → terminé. Si problème → rollback (cf. section Rollback)
```

## 💡 Tips & Bonnes Pratiques

1. **Immutabilité des images** : Ne poussez jamais une image avec le même tag deux fois. Utilisez des tags immuables (v4.8.0, pas 'latest') pour la production.

2. **Secrets sécurisés** : Ne stockez jamais `config/secrets.json` dans Docker ou git. Utilisez `--copy-secrets` ou variables d'environnement.

3. **Backup BD avant migration** : Si votre release inclut une migration de schéma, backupez la DB avant déploiement.

4. **Logs centralisés** : Gardez un historique des logs de déploiement (`ssh host 'docker compose logs' > deploy-$(date +%s).log`).

5. **Alertes santé** : Configurez un monitoring (ping `/health` toutes les minutes) pour détecter les régressions rapidement.

6. **Feature flags** : Pour les changements sensibles, déployez le code avec la feature désactivée par défaut, puis activez progressivement en production.

---

**Questions ?** Adaptez ce guide à votre workflow exact et partagez vos conventions d'équipe.
