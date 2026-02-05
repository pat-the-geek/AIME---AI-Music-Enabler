# AIME Services Management

Outils de démarrage et gestion des services AIME (Roon Bridge + Backend + Frontend).

## Quick Start

### 1. Démarrer tous les services
```bash
./scripts/start-services.sh
```

Cela va:
- ✅ Lancer le Roon Bridge (port 3330)
- ✅ Lancer le backend Python FastAPI (port 8000)
- ✅ Lancer le frontend React (port 5173)
- 📊 Monitorer tous les services avec auto-restart

### 2. Arrêter tous les services
```bash
./scripts/stop-services.sh
```

## Scripts Disponibles

### `start-services.sh`
Lance le bridge, backend, et frontend avec monitoring automatique.

**Features:**
- Détecte les ports déjà en usage et les nettoie
- Vérifie les prérequis (Node.js, Python venv)
- Valide la permissions des répertoires
- Attend que chaque service soit prêt avant de continuer
- Re-démarre automatiquement les services qui crashent
- Affiche les logs en direct

**Endpoints disponibles:**
```
🌉 Roon Bridge: http://localhost:3330/status
🎵 Backend:     http://localhost:8000/api/v1/roon/zones
📚 API Docs:    http://localhost:8000/docs
⚛️  Frontend:    http://localhost:5173
```

### `stop-services.sh`
Arrête proprement tous les services.

**Features:**
- Tue les processus Node et Python
- Nettoie les fichiers PID
- Vérifie que tout est bien arrêté

### `install-launch-agent.sh` (macOS uniquement)
Configure le Roon Bridge pour démarrer automatiquement au login.

**Installation:**
```bash
./scripts/install-launch-agent.sh
```

**Après installation:**
- 🚀 Le bridge démarre automatiquement à chaque login macOS
- 📋 Vérifier le statut: `launchctl list | grep roon-bridge`
- 📝 Voir les logs: `tail -f /tmp/aime_bridge.log`
- 🔄 Recharger: `launchctl unload ~/Library/LaunchAgents/com.aime.roon-bridge.plist && launchctl load ~/Library/LaunchAgents/com.aime.roon-bridge.plist`
- 🗑️  Désinstaller: `rm ~/Library/LaunchAgents/com.aime.roon-bridge.plist`

## Dossiers de Logs

Tous les logs sont dans `/tmp/`:
```bash
tail -f /tmp/aime_bridge.log      # Logs du bridge
tail -f /tmp/aime_backend.log     # Logs du backend
tail -f /tmp/aime_frontend.log    # Logs du frontend
```

Ou utiliser les chemins du projet:
```bash
tail -f backend/server.log        # Backend logs
tail -f roon-bridge/bridge.log    # Bridge logs
```

## Variables d'Environnement

### Roon Bridge
```bash
export ROON_BRIDGE_PORT=3330      # Port d'écoute HTTP (défaut: 3330)
export CONFIG_DIR=./config        # Répertoire de config (défaut: ./config)
```

### Backend Python
```bash
export UVICORN_HOST=0.0.0.0       # Bind à toutes les interfaces
export UVICORN_PORT=8000          # Port (défaut: 8000)
export UVICORN_WORKERS=1          # Nombre de workers
```

## Dépannage

### Le bridge ne démarre pas
```bash
# Vérifier que Node.js est installé
node --version

# Vérifier que le port 3330 est libre
lsof -i :3330

# Voir les erreurs détaillées
tail -f /tmp/aime_bridge.log
```

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
# Bridge
curl http://localhost:3330/status

# Backend
curl http://localhost:8000/api/v1/roon/zones

# Frontend
curl http://localhost:5173
```

### Monitorer les ports
```bash
lsof -i :3330  # Bridge
lsof -i :8000  # Backend
lsof -i :5173  # Frontend (si en dev)
```

### Voir les PIDs
```bash
cat /tmp/aime_pids/bridge.pid
cat /tmp/aime_pids/backend.pid
cat /tmp/aime_pids/frontend.pid
```

### Tuer manuellement un service
```bash
kill -9 $(lsof -ti :3330)  # Bridge
kill -9 $(lsof -ti :8000)  # Backend
kill -9 $(lsof -ti :5173)  # Frontend
```

## macOS LaunchAgent

Le LaunchAgent `com.aime.roon-bridge` redémarre automatiquement le bridge s'il crash:
- ✅ Auto-start au login
- ✅ Auto-restart si crash
- ✅ Max 10 redémarrages avant de s'arrêter
- 📝 Logs dans `/tmp/aime_bridge.log`

### Configuration du LaunchAgent
```bash
# Voir la config
cat ~/Library/LaunchAgents/com.aime.roon-bridge.plist

# Désactiver le auto-restart
launchctl unload ~/Library/LaunchAgents/com.aime.roon-bridge.plist

# Réactiver
launchctl load ~/Library/LaunchAgents/com.aime.roon-bridge.plist
```

## Performance

### Optimization Tips:

1. **Roon Bridge:**
   - Écoute sur tous les ports: `0.0.0.0:3330`
   - Timeout SOOD: 5 secondes (pour Roon discovery)
   - Browse mutex: Sérialise les requêtes (pas de race conditions)

2. **Backend:**
   - Workers: 1 (single-worker pour simplicité)
   - Timeout: 15 secondes pour playback
   - Reload: Activé pour développement

3. **Frontend:**
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
