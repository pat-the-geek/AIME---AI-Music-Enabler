# AIME Services Management

Outils de démarrage et gestion des services AIME (Backend + Frontend).

## Quick Start

### 1. Démarrer tous les services
```bash
./scripts/start-services.sh
```

Cela va:
- ✅ Lancer le backend Python FastAPI (port 8000)
- ✅ Lancer le frontend React (port 5173)
- 📊 Monitorer les services avec auto-restart

### 2. Arrêter tous les services
```bash
./scripts/stop-services.sh
```

## Scripts Disponibles

### `start-services.sh`
Lance le backend et le frontend avec monitoring automatique.

**Features:**
- Détecte les ports déjà en usage et les nettoie
- Vérifie les prérequis (Node.js, Python venv)
- Valide la permissions des répertoires
- Attend que chaque service soit prêt avant de continuer
- Re-démarre automatiquement les services qui crashent
- Affiche les logs en direct

**Endpoints disponibles:**
```
🎵 Backend:  http://localhost:8000
📚 API Docs: http://localhost:8000/docs
⚛️  Frontend: http://localhost:5173
```

### `stop-services.sh`
Arrête proprement tous les services.

**Features:**
- Tue les processus Node et Python
- Nettoie les fichiers PID
- Vérifie que tout est bien arrêté

## Dossiers de Logs

Tous les logs sont dans `/tmp/`:
```bash
tail -f /tmp/aime_backend.log     # Logs du backend
tail -f /tmp/aime_frontend.log    # Logs du frontend
```

Ou utiliser les chemins du projet:
```bash
tail -f backend/server.log        # Backend logs
```

## Variables d'Environnement

### Backend Python
```bash
export UVICORN_HOST=0.0.0.0       # Bind à toutes les interfaces
export UVICORN_PORT=8000          # Port (défaut: 8000)
export UVICORN_WORKERS=1          # Nombre de workers
```

## Dépannage

### Le backend ne démarre pas
```bash
# Vérifier que Python venv existe
ls backend/.venv

# Vérifier les dépendances
backend/.venv/bin/pip list | grep -E "fastapi|httpx|uvicorn"

# Voir les erreurs détaillées
tail -f backend/server.log
```

### Remise à zéro complète
```bash
# 1. Arrêter tous les services
./scripts/stop-services.sh

# 2. Nettoyer les ports
lsof -ti :3330 | xargs kill -9 2>/dev/null || true
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true

# 3. Nettoyer les caches
rm -rf backend/__pycache__
rm -rf backend/.pytest_cache
rm -f /tmp/aime_*.log
rm -rf /tmp/aime_pids

# 4. Redémarrer
./scripts/start-services.sh
```

## Commands Utiles

### Vérifier la santé des services
```bash
# Backend
curl http://localhost:8000

# Frontend
curl http://localhost:5173
```

### Monitorer les ports
```bash
lsof -i :8000  # Backend
lsof -i :5173  # Frontend (si en dev)
```

## Performance

### Optimization Tips:

1. **Backend:**
   - Workers: 1 (single-worker pour simplicité)
   - Timeout: 15 secondes
   - Reload: Activé pour développement

2. **Frontend:**
   - Vite dev server (HMR actif)
   - Port: 5173

### Métriques
```bash
# Temps de démarrage moyen
time ./scripts/start-services.sh

# Mémoire utilisée
ps aux | grep -E "node app.js|python.*uvicorn"

# Connexions réseau
netstat -an | grep -E "3330|8000|5173"
```

## Support & Issues

Si un service refuse de démarrer:

1. **Vérifier les logs:**
   ```bash
   tail -f /tmp/aime_*.log
   ```

2. **Nettoyer les ports:**
   ```bash
   ./scripts/stop-services.sh  # Arrêter proprement
   killall node python         # Forcer le kill
   ```

3. **Réinstaller les dépendances:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt --force-reinstall
   
   # Bridge
   cd roon-bridge
   npm install
   ```

4. **Reset complet:**
   ```bash
   ./scripts/stop-services.sh
   rm -rf backend/.venv
   python3 -m venv backend/.venv
   backend/.venv/bin/pip install -r backend/requirements.txt
   npm install --prefix roon-bridge
   ./scripts/start-services.sh
   ```
