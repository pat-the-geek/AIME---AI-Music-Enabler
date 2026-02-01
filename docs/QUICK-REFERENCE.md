# Quick Reference - AIME Robustness

## 🚀 Démarrage Immédiat

```bash
# 1. Valider tout est prêt
cd backend && python validate_startup.py && cd ..

# 2. Démarrer (tout automatique)
./scripts/start-services.sh

# 3. Vérifier la santé
curl http://localhost:8000/health
```

## ✅ Vérifications Rapides

```bash
# Backend OK?
curl -f http://localhost:8000/health

# Frontend OK?
curl -f http://localhost:5173

# Readiness (Kubernetes)
curl -f http://localhost:8000/ready

# Tests complets
./scripts/test-robustness.sh
```

## 🔧 Dépannage Rapide

| Problème | Solution |
|----------|----------|
| Port 8000 en conflit | `lsof -ti :8000 \| xargs kill -9` |
| Port 5173 en conflit | `lsof -ti :5173 \| xargs kill -9` |
| DB corrompue | `rm data/musique.db && restart` |
| Dépendances manquantes | `pip install -r backend/requirements.txt` |
| Frontend ne se charge | `cd frontend && npm ci && npm run dev` |
| Logs backend | `tail -f /tmp/aime_backend.log` |
| Logs frontend | `tail -f /tmp/aime_frontend.log` |

## 📊 Monitoring

```bash
# Suivi en continu
tail -f /tmp/aime_backend.log

# Statut des services
curl http://localhost:8000/health | jq

# Utilisation des ressources
top -p $(cat /tmp/aime_pids/backend.pid)
```

## 🐳 Docker Compose

```bash
# Init DB une fois
docker-compose run --rm init-db

# Démarrer
docker-compose up -d

# Logs
docker-compose logs -f backend

# Arrêter
docker-compose down

# Redémarrer complètement
docker-compose down && docker-compose up -d
```

## 📋 Checklist Déploiement

- [ ] `python validate_startup.py` → OK
- [ ] `/health` → `healthy`
- [ ] `/ready` → `ready: true`
- [ ] `/api/v1/collection/albums` → 200
- [ ] `./scripts/test-robustness.sh` → PASS
- [ ] Logs normaux (pas d'erreurs)
- [ ] Redémarrage complète → OK

## 🔑 Points Clés

### Auto-restart
- Backend: Redémarre auto après 3 échecs
- Frontend: Redémarre auto après 3 échecs
- Timeout: <60 secondes

### Health Checks
- Toutes les 30 secondes
- Retries automatiques
- Logs détaillés en cas d'erreur

### Database
- WAL mode (concurrence safe)
- Pool gestion automatique
- Recycling connexions (1h)

### Logs
- `/tmp/aime_backend.log` → backend
- `/tmp/aime_frontend.log` → frontend
- Docker → `docker-compose logs`

## 🎯 Commandes Essentielles

```bash
# Démarrer
./scripts/start-services.sh

# Arrêter (Ctrl+C dans le terminal)

# Tester la santé
./scripts/health-check-robust.sh health

# Tester la préparation
./scripts/health-check-robust.sh ready

# Tests complets
./scripts/test-robustness.sh

# Valider avant démarrage
cd backend && python validate_startup.py

# Logs
tail -f /tmp/aime_backend.log
tail -f /tmp/aime_frontend.log
```

## 📖 Documentation Complète

- **RELIABILITY-GUIDE.md** → Guide détaillé
- **ROBUSTNESS-IMPROVEMENTS-V4.md** → Changements
- **backend/validate_startup.py** → Validation
- **scripts/start-services.sh** → Démarrage
- **docker-compose.yml** → Production

## 🆘 Aide Rapide

```bash
# Afficher le statut
curl http://localhost:8000/health | jq .status

# Afficher les erreurs
curl http://localhost:8000/health | jq .last_error

# Taux d'erreur
curl http://localhost:8000/health | jq .error_rate

# Uptime
curl http://localhost:8000/health | jq .uptime_seconds
```

---

**TL;DR**: `./scripts/start-services.sh` et c'est tout! ✅
