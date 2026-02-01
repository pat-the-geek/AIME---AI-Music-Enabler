# 🔧 Correction: Zone Roon Non Trouvée au Redémarrage

## 🐛 Problème Identifié

Lors du redémarrage automatique des services, le tracker Roon ne trouvait pas la zone par défaut et la liste des zones était vide. Cela se produisait car :

1. La connexion Roon prend du temps (jusqu'à 15 secondes)
2. Les zones ne sont pas immédiatement disponibles après la connexion
3. Le tracker démarrait avant que les zones soient chargées

## ✅ Solutions Implémentées

### 1. Attente des Zones dans RoonService

**Fichier**: `backend/app/services/roon_service.py`

Après connexion, le service attend maintenant jusqu'à 3 secondes que les zones soient disponibles :

```python
# Attendre que les zones soient chargées
max_wait = 3  # Attendre max 3 secondes
for i in range(max_wait):
    if hasattr(self.roon_api, 'zones') and self.roon_api.zones:
        self.zones = self.roon_api.zones
        logger.info(f"✅ {len(self.zones)} zone(s) Roon disponible(s)")
        break
    time.sleep(1)
else:
    logger.warning("⚠️ Aucune zone Roon trouvée après connexion")
```

### 2. Vérification des Zones dans RoonTrackerService

**Fichier**: `backend/app/services/roon_tracker_service.py`

Le tracker vérifie maintenant que les zones sont disponibles avant de démarrer :

```python
# Vérifier que les zones sont disponibles
zones = self.roon.get_zones()
if not zones:
    logger.warning("⚠️ Aucune zone Roon disponible - attente de la mise à jour des zones...")
    # Attendre un peu que les zones soient chargées (jusqu'à 5 secondes)
    for i in range(5):
        await asyncio.sleep(1)
        zones = self.roon.get_zones()
        if zones:
            logger.info(f"✅ Zones Roon disponibles: {list(zones.keys())}")
            break
    
    if not zones:
        logger.error("❌ Impossible de démarrer le tracker Roon: aucune zone disponible après 5s")
        return
```

### 3. Délai Supplémentaire dans restore_active_services()

**Fichier**: `backend/app/api/v1/services.py`

Lors de la restauration automatique, on attend 2 secondes supplémentaires avant de démarrer le tracker Roon :

```python
elif service_name == 'roon_tracker':
    # Pour Roon, attendre un peu plus que les zones soient disponibles
    logger.info(f"⏳ Attente connexion Roon avant restauration du tracker...")
    await asyncio.sleep(2)  # Donner 2s de plus à Roon pour se connecter
    
    roon_tracker = get_roon_tracker()
    await roon_tracker.start()
    logger.info(f"✅ Tracker Roon restauré")
```

## 📋 Séquence de Démarrage Améliorée

### Avant la Correction
```
1. Serveur démarre
2. restore_active_services() s'exécute
3. RoonService se connecte (timeout 15s)
4. Tracker démarre immédiatement ❌ Zones vides!
```

### Après la Correction
```
1. Serveur démarre
2. restore_active_services() s'exécute
3. Attente 2s pour la connexion Roon
4. RoonService se connecte
   - Connexion établie
   - Attente zones (max 3s)
   - ✅ Zones chargées
5. Tracker vérifie zones disponibles
   - Si vides: attente 5s max
   - ✅ Zones disponibles
6. Tracker démarre avec succès
```

## 🧪 Test de Validation

### Prérequis
- Serveur Roon en marche
- Configuration correcte dans `config/app.json` (roon_server)

### Procédure de Test

1. **Démarrer les services**
```bash
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
./scripts/start-dev.sh
```

2. **Activer le tracker Roon**
```bash
curl -X POST "http://localhost:8000/api/v1/services/roon-tracker/start"
```

3. **Vérifier le statut**
```bash
curl "http://localhost:8000/api/v1/services/roon-tracker/status"
```

**Résultat attendu**:
```json
{
  "running": true,
  "interval": 120,
  "last_poll": "2026-02-01T18:00:00.123456",
  "last_track_found": null
}
```

4. **Redémarrer le serveur**
```bash
# Arrêter (Ctrl+C ou)
pkill -f "uvicorn"

# Redémarrer
./scripts/start-dev.sh
```

5. **Observer les logs au démarrage**

**Logs attendus** (chronologiques):
```
2026-02-01 18:05:00 - app.main - INFO - 🚀 Démarrage de l'application AIME
2026-02-01 18:05:00 - app.api.v1.services - INFO - 🔄 Restauration des services actifs...
2026-02-01 18:05:00 - app.api.v1.services - INFO - ⏳ Attente connexion Roon avant restauration du tracker...
2026-02-01 18:05:02 - app.services.roon_service - INFO - ✅ 2 zone(s) Roon disponible(s)
2026-02-01 18:05:02 - app.services.roon_service - INFO - ✅ Connecté au serveur Roon: 192.168.1.100:9330
2026-02-01 18:05:02 - app.services.roon_tracker_service - INFO - ✅ Zones Roon disponibles: ['zone_id_1', 'zone_id_2']
2026-02-01 18:05:02 - app.services.roon_tracker_service - INFO - 🎵 Tracker Roon démarré (intervalle: 120s)
2026-02-01 18:05:02 - app.api.v1.services - INFO - ✅ Tracker Roon restauré
```

6. **Vérifier depuis le frontend**
   - Ouvrir http://localhost:5173/settings
   - Section "Tracker Roon" doit afficher:
     - ✅ Badge vert "Le tracker est actif"
     - Liste des zones disponibles
     - Bouton "Arrêter le Tracker"

## 🔍 Debugging

### Problème: Zones toujours vides

**Vérifier dans les logs**:
```bash
tail -f backend/logs/app.log | grep -i "zone"
```

**Diagnostics possibles**:

1. **Serveur Roon non accessible**
```
⚠️ Timeout connexion Roon après 15s - serveur peut être inaccessible
```
→ Vérifier l'adresse IP dans `config/app.json`

2. **Pas de zones actives dans Roon**
```
⚠️ Aucune zone Roon trouvée après connexion
```
→ Démarrer une zone dans l'application Roon

3. **Token invalide**
```
❌ Erreur connexion Roon: ...
```
→ Supprimer le token dans `config/app.json` et réautoriser l'app

### Commandes Utiles

**Vérifier les zones via API**:
```bash
curl "http://localhost:8000/api/v1/roon/zones"
```

**Forcer une reconnexion Roon**:
```bash
# Arrêter le tracker
curl -X POST "http://localhost:8000/api/v1/services/roon-tracker/stop"

# Attendre 5s
sleep 5

# Redémarrer
curl -X POST "http://localhost:8000/api/v1/services/roon-tracker/start"
```

**Vérifier le statut global**:
```bash
curl "http://localhost:8000/api/v1/services/status/all"
```

## 📊 Indicateurs de Succès

✅ **Connexion établie**: Log "Connecté au serveur Roon"  
✅ **Zones chargées**: Log "X zone(s) Roon disponible(s)"  
✅ **Tracker démarré**: Log "Tracker Roon démarré"  
✅ **Zones visibles**: Frontend affiche la liste des zones  
✅ **Auto-restart**: Tracker redémarre après reboot serveur  

## 📁 Fichiers Modifiés

- `backend/app/services/roon_service.py` - Attente des zones après connexion
- `backend/app/services/roon_tracker_service.py` - Vérification zones avant démarrage
- `backend/app/api/v1/services.py` - Délai supplémentaire pour Roon

## 🎯 Améliorations Futures

- [ ] Retry automatique si zones vides
- [ ] Configuration du délai d'attente
- [ ] Notification si échec connexion Roon
- [ ] Métriques de disponibilité des zones
- [ ] Reconnexion automatique en cas de perte

---

**Version**: 1.0  
**Date**: 1er février 2026  
**Fix**: Zones Roon disponibles après auto-restart
