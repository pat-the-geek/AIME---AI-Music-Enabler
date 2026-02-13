# 🔄 Auto-Restart des Services - Guide de Test

## ✅ Fonctionnalité Implémentée

Les services background (Tracker Last.fm et Scheduler) redémarrent automatiquement après un redémarrage du serveur s'ils étaient actifs.

## 🏗️ Architecture

### Composants Créés

1. **Modèle de Persistance** : `backend/app/models/service_state.py`
   - Table SQLite `service_states` stockant l'état de chaque service
   - Colonnes : `service_name`, `is_active`, `last_updated`

2. **Logique de Sauvegarde** : `backend/app/api/v1/services.py`
   - `save_service_state()` : Sauvegarde l'état dans la DB
   - `get_service_state()` : Récupère l'état depuis la DB
   - `restore_active_services()` : Restaure les services actifs au démarrage
   - Modifié tous les endpoints start/stop pour persister l'état

3. **Intégration Startup** : `backend/app/main.py`
   - Appel de `restore_active_services()` dans la fonction `lifespan()`
   - Exécuté automatiquement au démarrage du serveur

4. **Migration DB** : `backend/alembic/versions/003_add_service_states.py`
   - Crée la table `service_states` avec index
   - Script helper : `backend/create_service_states_table.py`

## 🧪 Tests Automatisés

```bash
cd backend
python3 test_auto_restart.py
```

**Résultat attendu** :
```
✅ TOUS LES TESTS RÉUSSIS!
📋 Résumé:
   ✓ Table service_states créée
   ✓ États peuvent être sauvegardés
   ✓ États peuvent être lus
   ✓ États peuvent être mis à jour
   ✓ Logique de restauration fonctionnelle
```

## 📋 Test Manuel - Procédure Complète

### 1. Démarrage Initial

```bash
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
./scripts/start-dev.sh
```

**Logs attendus** :
```
2026-02-01 17:37:02 - app.main - INFO - 🚀 Démarrage de l'application AIME
2026-02-01 17:37:02 - app.main - INFO - ✅ Base de données initialisée
2026-02-01 17:37:02 - app.api.v1.services - INFO - 🔄 Restauration des services actifs...
2026-02-01 17:37:02 - app.api.v1.services - INFO - ℹ️ Aucun service actif à restaurer
2026-02-01 17:37:02 - app.main - INFO - ✅ Application ready to serve requests
```

### 2. Activer un Service

**Option A - Via Frontend** :
1. Ouvrir http://localhost:5173
2. Aller dans **Settings**
3. Cliquer sur **"Démarrer le Tracker"** (Last.fm)

**Option B - Via API** :
```bash
curl -X POST "http://localhost:8000/api/v1/services/tracker/start"
```

**Réponse attendue** :
```json
{"status":"started"}
```

**Log backend attendu** :
```
2026-02-01 17:40:00 - app.services.tracker_service - INFO - 🎵 Tracker Last.fm démarré
2026-02-01 17:40:00 - app.api.v1.services - INFO - 💾 État du service 'tracker' sauvegardé: actif
```

### 3. Vérifier l'État

```bash
curl "http://localhost:8000/api/v1/services/tracker/status"
```

**Réponse attendue** :
```json
{
  "running": true,
  "interval": 120,
  "last_check": "2026-02-01T17:40:00.123456",
  "tracks_found": 0
}
```

### 4. Redémarrer le Serveur

**Arrêter** :
```bash
# Ctrl+C dans le terminal où tourne start-dev.sh
# OU
pkill -f "uvicorn"
```

**Redémarrer** :
```bash
./scripts/start-dev.sh
```

### 5. Vérifier la Restauration Automatique

**Logs attendus au démarrage** :
```
2026-02-01 17:42:00 - app.main - INFO - 🚀 Démarrage de l'application AIME
2026-02-01 17:42:00 - app.main - INFO - ✅ Base de données initialisée
2026-02-01 17:42:00 - app.api.v1.services - INFO - 🔄 Restauration des services actifs...
2026-02-01 17:42:00 - app.services.tracker_service - INFO - 🎵 Tracker Last.fm démarré
2026-02-01 17:42:00 - app.api.v1.services - INFO - ✅ Tracker Last.fm restauré
2026-02-01 17:42:00 - app.main - INFO - ✅ Application ready to serve requests
```

**Vérification API** :
```bash
curl "http://localhost:8000/api/v1/services/tracker/status"
```

**Résultat attendu** : `"running": true` ✅

### 6. Vérifier le Frontend

1. Ouvrir http://localhost:5173/settings
2. Section **"Tracker Last.fm"** doit afficher :
   - Badge vert **"✅ Le tracker est actif"**
   - Bouton rouge **"Arrêter le Tracker"**
   - Dernière vérification visible

## 🧬 Test avec Plusieurs Services

```bash
# Démarrer tracker Last.fm
curl -X POST "http://localhost:8000/api/v1/services/tracker/start"

# Démarrer scheduler
curl -X POST "http://localhost:8000/api/v1/services/scheduler/start"

# Vérifier tous les états
curl "http://localhost:8000/api/v1/services/status/all"
```

**Redémarrer le serveur** → Les 2 services doivent se restaurer automatiquement.

## 🔍 Vérification Base de Données

```bash
cd backend
python3 -c "
from app.database import SessionLocal
from app.models import ServiceState

db = SessionLocal()
states = db.query(ServiceState).all()
for state in states:
    status = '✅' if state.is_active else '⏸️'
    print(f'{status} {state.service_name} - MAJ: {state.last_updated}')
db.close()
"
```

**Exemple de sortie** :
```
✅ tracker - MAJ: 2026-02-01 17:40:00.123456
✅ scheduler - MAJ: 2026-02-01 17:40:05.789012
```

## 🐛 Troubleshooting

### Problème : Les services ne redémarrent pas

**1. Vérifier que la table existe** :
```bash
cd backend
python3 create_service_states_table.py
```

**2. Vérifier les logs au démarrage** :
```
tail -f backend/logs/app.log | grep "Restauration"
```

**3. Vérifier la base de données** :
```bash
sqlite3 backend/data/musique.db "SELECT * FROM service_states;"
```

### Problème : Erreur "no such table: service_states"

**Solution** :
```bash
cd backend
python3 create_service_states_table.py
```

### Problème : Services restaurés mais pas visibles dans le frontend

**Solution** :
1. Rafraîchir la page (F5)
2. Vérifier que le frontend communique avec le backend :
```bash
curl "http://localhost:8000/api/v1/services/status/all"
```

## 📊 Indicateurs de Succès

✅ **Persistence** : État sauvegardé dans `service_states` après start/stop  
✅ **Restauration** : Logs "✅ [Service] restauré" au démarrage  
✅ **API** : Statut `"running": true` après redémarrage  
✅ **Frontend** : Badge vert et bouton "Arrêter" visible  
✅ **Stabilité** : Aucune erreur dans les logs  

## 📁 Fichiers Modifiés/Créés

### Nouveaux Fichiers
- `backend/app/models/service_state.py` - Modèle DB
- `backend/alembic/versions/003_add_service_states.py` - Migration
- `backend/create_service_states_table.py` - Script de création table
- `backend/test_auto_restart.py` - Tests automatisés
- `AUTO-RESTART-TEST-GUIDE.md` - Ce guide

### Fichiers Modifiés
- `backend/app/models/__init__.py` - Ajout import ServiceState
- `backend/app/api/v1/services.py` - Logique de persistance
- `backend/app/main.py` - Appel restore_active_services()

## 🎯 Prochaines Étapes

Pour aller plus loin :
- [ ] Interface UI pour visualiser l'historique des états
- [ ] Configuration du délai avant auto-restart
- [ ] Notifications en cas d'échec de restauration
- [ ] Métriques de disponibilité des services

---

**Version** : 1.0  
**Date** : 1er février 2026  
**Auteur** : Patrick Ostertag (avec GitHub Copilot)
