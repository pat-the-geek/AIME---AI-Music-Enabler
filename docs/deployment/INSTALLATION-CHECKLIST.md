# 📋 Checklist de Configuration Stable

## Avant de Démarrer

### 1. Environnement Python ✅
- [ ] Python 3.10+ installé: `python3 --version`
- [ ] Virtual env créé: `cd backend && source .venv/bin/activate`
- [ ] Dépendances installées: `pip install -r requirements.txt`

### 2. Environnement Node.js ✅
- [ ] Node 18+ installé: `node --version`
- [ ] npm 9+ installé: `npm --version`
- [ ] Dépendances frontend: `cd frontend && npm install`

### 3. Configuration ✅
- [ ] `.env.example` copié en `.env` (si nécessaire)
- [ ] Clés API configurées (facultatif pour démarrage)
- [ ] Base de données disponible: `data/music_tracker.db`

---

## Démarrage

### Option 1: Script Amélioré (Recommandé)
```bash
./scripts/start-dev.sh
```
**Avantages**: Gestion automatique des ports, retry logic, cleanup

### Option 2: Manuel
```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## Vérification du Démarrage

### Commande Rapide
```bash
./scripts/health-check.sh
```

### Manuel
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:5173 | head -20

# Données
curl http://localhost:8000/api/v1/history/stats | jq .
```

---

## Ports Utilisés

| Service | Port | URL |
|---------|------|-----|
| Backend | 8000 | http://localhost:8000 |
| Frontend | 5173 | http://localhost:5173 |
| Docs API | 8000/docs | http://localhost:8000/docs |

---

## En Cas de Problème

| Problème | Solution |
|----------|----------|
| "Port 8000 in use" | `./scripts/health-check.sh` puis `./scripts/start-dev.sh` |
| Backend ne répond pas | Vérifier: `curl http://localhost:8000/health` |
| Frontend blanc | Attendre le build Vite (60s max) |
| DB corrompue | `rm data/music_tracker.db` et redémarrer |

**Guide complet**: [docs/TROUBLESHOOTING-INFRASTRUCTURE.md](../TROUBLESHOOTING-INFRASTRUCTURE.md)

---

## Architecture Globale

```
Backend (FastAPI)
├── SQLite DB
├── API REST /api/v1/*
└── Services (Spotify, Last.fm, Discogs, IA)

Frontend (React + Vite)
├── Pages: Collection, Journal, Timeline, Playlists, Analytics
└── API Client → Backend
```

---

## Points d'Entrée

- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

**Status**: ✅ Infrastructure Stable
**Dernière mise à jour**: 31 janvier 2026
