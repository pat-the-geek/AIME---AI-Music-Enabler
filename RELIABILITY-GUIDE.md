# Guide de Fiabilité et Déploiement - AIME

## 🔧 Améliorations Récentes de Fiabilité

### 1. **Health Monitoring Robuste**
- Endpoint `/health` : Vérification complète de la santé de l'application
- Endpoint `/ready` : Readiness probe pour les orchestrateurs (Kubernetes, Docker)
- Monitoring de la base de données avec métriques
- Détection automatique des modes dégradés

### 2. **Démarrage Validé**
Le système effectue désormais une validation complète au démarrage :
```python
- ✅ Vérification de la base de données
- ✅ Import de tous les modules critiques
- ✅ Validation des répertoires de données
- ✅ Vérification des permissions
```

### 3. **Gestion d'Erreurs Améliorée**
- Try-finally blocks pour cleanup des ressources
- Logging détaillé des erreurs
- Graceful shutdown avec timeout
- Retry logic avec backoff exponentiel

### 4. **Script de Démarrage Robuste**
Le nouveau `start-services.sh` :
- Vérifie tous les prérequis avant le démarrage
- Crée automatiquement les répertoires nécessaires
- Installe les dépendances manquantes
- Monitore en continu et redémarre automatiquement
- Affichage clair du statut avec couleurs

## 🚀 Utilisation

### Démarrage Local
```bash
# Validation préalable
cd backend
python validate_startup.py
cd ..

# Démarrage normal
./scripts/start-services.sh
```

### Vérification de Santé
```bash
# Health check basique
curl http://localhost:8000/health

# Readiness check (pour Kubernetes/Docker)
curl http://localhost:8000/ready

# Script de vérification robuste
./scripts/health-check-robust.sh health
./scripts/health-check-robust.sh ready
```

### Docker Compose (Production)
```bash
# Première initialisation
docker-compose run --rm init-db

# Démarrage
docker-compose up -d

# Vérifier les logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Arrêt propre
docker-compose down
```

## 📊 Configuration Docker Compose

Le fichier `docker-compose.yml` inclut maintenant :

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Dépendances Orchestrées
```yaml
depends_on:
  backend:
    condition: service_healthy  # Frontend attend que le backend soit sain
```

### Logging
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔍 Diagnostic des Problèmes

### Le backend ne démarre pas

1. **Vérifier les logs**
   ```bash
   tail -f /tmp/aime_backend.log
   ```

2. **Valider la configuration**
   ```bash
   cd backend
   python validate_startup.py
   ```

3. **Tester la base de données**
   ```bash
   sqlite3 data/musique.db "SELECT COUNT(*) FROM albums;"
   ```

4. **Vérifier les ports**
   ```bash
   lsof -i :8000
   ```

### Le frontend ne démarre pas

1. **Vérifier les logs**
   ```bash
   tail -f /tmp/aime_frontend.log
   ```

2. **Vérifier les dépendances npm**
   ```bash
   cd frontend
   npm ci --prefer-offline
   ```

3. **Nettoyer et reconstruire**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

### Connexion lente ou timeouts

1. **Augmenter les timeouts dans le backend**
   - Éditer `backend/app/core/config.py`
   - Modifier `timeout_keep_alive` et `timeout_graceful_shutdown`

2. **Optimiser la base de données**
   ```bash
   sqlite3 data/musique.db "VACUUM; ANALYZE;"
   ```

3. **Vérifier les ressources système**
   ```bash
   top
   df -h
   ```

## 🛡️ Points Critiques de Fiabilité

### Base de Données
- ✅ Pool de connexions géré automatiquement
- ✅ WAL mode activé pour SQLite
- ✅ Vérification des connexions avant usage
- ✅ Recycling des connexions toutes les heures

### API
- ✅ Exception handling globale
- ✅ Validation des entrées Pydantic
- ✅ Request timeout de 75 secondes
- ✅ Graceful shutdown de 30 secondes

### Monitoring
- ✅ Health check toutes les 30 secondes
- ✅ Auto-restart en cas d'échec (3 tentatives)
- ✅ Taux d'erreur suivi
- ✅ Uptime monitoring

## 📈 Métriques de Santé

L'endpoint `/health` retourne :
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "requests": 1234,
  "errors": 5,
  "error_rate": "0.41%",
  "database": "healthy",
  "last_db_check": "2026-01-31T12:00:00",
  "timestamp": "2026-01-31T12:01:00"
}
```

## 🔐 Sécurité et Stabilité

- ✅ CORS configuré correctement
- ✅ Validation de tous les inputs
- ✅ Gestion des erreurs sans fuite d'infos
- ✅ Logs structurés pour audit
- ✅ Graceful degradation en cas d'erreur

## 📝 Logs Importants

### Backend
- `/tmp/aime_backend.log` : Logs de l'application
- Inclut les erreurs, les avertissements et les infos

### Frontend  
- `/tmp/aime_frontend.log` : Logs du serveur Vite

### Docker
```bash
docker-compose logs backend
docker-compose logs frontend
```

## ✅ Checklist de Déploiement

- [ ] Exécuter `validate_startup.py`
- [ ] Vérifier `/health` retourne `status: healthy`
- [ ] Vérifier `/ready` retourne `ready: true`
- [ ] Tester les endpoints principaux
- [ ] Vérifier la création/modification de données
- [ ] Vérifier les exports (JSON, Markdown)
- [ ] Monitorer les logs pendant 5 minutes
- [ ] Tester un redémarrage complet

## 🔄 Redémarrage Complet

```bash
# Arrêt propre
./scripts/start-services.sh  # Ctrl+C

# Attendre 5 secondes
sleep 5

# Redémarrage
./scripts/start-services.sh
```

Le système devrait redémarrer automatiquement sans intervention supplémentaire.
