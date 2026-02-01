# 🐛 Bugs Roon - Suivi et Investigation

**Date de création:** 1er février 2026  
**Version:** 4.3.1  
**Status:** 🔴 En cours d'investigation

---

## 📋 Vue d'ensemble

Ce document trace les bugs identifiés dans l'intégration Roon et les investigations en cours pour les résoudre.

## 🔴 Bug #1: Démarrage des Lectures Instable

### Description

Le démarrage des lectures dans Roon via les commandes AIME (Play, Pause, Next) peut échouer ou avoir un comportement incohérent.

### Symptômes Observés

1. ❌ Commande `/api/v1/roon/play` retourne 200 OK mais lecture ne démarre pas
2. ⏱️ Délai imprévisible entre l'envoi de la commande et le démarrage effectif
3. 🔄 Nécessité de répéter plusieurs fois la commande pour qu'elle fonctionne
4. 🎯 Comportement aléatoire selon les zones Roon

### Contexte Technique

**Endpoint concerné:**
```python
POST /api/v1/roon/play
POST /api/v1/roon/pause
POST /api/v1/roon/next
POST /api/v1/roon/previous
```

**Code actuel** (`backend/app/api/v1/roon.py`):
```python
@router.post("/play")
async def play():
    """Démarrer la lecture dans Roon."""
    roon_service.play()
    return {"status": "ok", "action": "play"}
```

**Service Roon** (`backend/app/services/roon_service.py`):
```python
def play(self) -> bool:
    """Démarrer la lecture sur la zone par défaut."""
    if not self.default_zone_id:
        logger.warning("Aucune zone par défaut définie")
        return False
    self.roon_api.playback_control(self.default_zone_id, 'play')
    return True
```

### Hypothèses

1. **Latence API pyroon:** La commande `playback_control()` peut être asynchrone
2. **État zone Roon:** La zone n'est peut-être pas dans un état valide pour recevoir la commande
3. **Callback manquant:** Pas de confirmation que la commande a été exécutée
4. **Default zone incorrect:** La zone par défaut peut changer dynamiquement

### Tests à Réaliser

- [ ] Logger le retour de `playback_control()` pour voir si erreur silencieuse
- [ ] Vérifier l'état de la zone avant d'envoyer la commande
- [ ] Tester avec zone_id explicite vs default_zone_id
- [ ] Ajouter callback de confirmation après commande
- [ ] Mesurer le temps entre commande et changement d'état

### Solutions Potentielles

#### Option 1: Vérification État Pré-Commande
```python
def play(self) -> bool:
    if not self.default_zone_id:
        return False
    
    # Vérifier que la zone existe et est prête
    zone = self.zones.get(self.default_zone_id)
    if not zone or zone.get('state') not in ['paused', 'stopped']:
        logger.warning(f"Zone {self.default_zone_id} not ready")
        return False
    
    self.roon_api.playback_control(self.default_zone_id, 'play')
    return True
```

#### Option 2: Callback de Confirmation
```python
def play(self) -> dict:
    result = {'success': False, 'message': ''}
    
    if not self.default_zone_id:
        result['message'] = 'No default zone'
        return result
    
    try:
        self.roon_api.playback_control(self.default_zone_id, 'play')
        # Attendre callback ou timeout 2s
        time.sleep(0.5)
        # Vérifier nouvel état
        zone = self.zones.get(self.default_zone_id)
        if zone and zone.get('state') == 'playing':
            result['success'] = True
            result['message'] = 'Playback started'
    except Exception as e:
        result['message'] = str(e)
    
    return result
```

#### Option 3: Retry Logic
```python
def play(self, max_retries: int = 3) -> bool:
    for i in range(max_retries):
        self.roon_api.playback_control(self.default_zone_id, 'play')
        time.sleep(0.3)
        zone = self.zones.get(self.default_zone_id)
        if zone and zone.get('state') == 'playing':
            return True
    return False
```

### Workaround Actuel

**Utilisateur:**
- Utiliser les contrôles natifs Roon directement
- Rafraîchir l'interface AIME pour mettre à jour l'état
- Éviter d'utiliser les commandes AIME pendant investigation

---

## 🔴 Bug #2: Désynchronisation État AIME ↔ Roon

### Description

L'état affiché dans l'interface AIME ne reflète pas toujours l'état réel de la lecture dans Roon.

### Symptômes Observés

1. 🎵 État "Playing" affiché dans AIME alors que Roon est en pause
2. 🎼 Track affiché obsolète après changement manuel dans Roon
3. ⏸️ Bouton Play/Pause dans mauvais état visuel
4. 🔄 Synchronisation retrouvée après 3-120 secondes (cycle polling)

### Contexte Technique

**Polling Frontend** (`frontend/src/contexts/RoonContext.tsx`):
```typescript
useEffect(() => {
  const interval = setInterval(() => {
    fetchRoonStatus();
  }, 3000); // 3s
  return () => clearInterval(interval);
}, []);
```

**Polling Backend** (`backend/app/services/roon_tracker_service.py`):
```python
scheduler = AsyncIOScheduler()
scheduler.add_job(track_listening, 'interval', seconds=120)
```

**Callback Zones** (`backend/app/services/roon_service.py`):
```python
def zones_callback(action, data):
    """Callback appelé quand les zones changent."""
    if action == 'zones_changed':
        roon_service.zones = roon_service.roon_api.zones
        logger.info(f"🔄 Zones Roon mises à jour: {len(roon_service.zones)} zone(s)")
```

### Hypothèses

1. **Callback non déclenché:** Les changements d'état ne déclenchent pas toujours le callback
2. **Cache zones obsolète:** `self.zones` n'est mis à jour que sur callback zones_changed
3. **Polling insuffisant:** 3s frontend / 120s backend trop lents pour actions manuelles
4. **État track non tracké:** Le callback `zones_changed` ne couvre pas tous les changements d'état

### Tests à Réaliser

- [ ] Logger tous les appels callback (action, data, timestamp)
- [ ] Vérifier si `zones_changed` inclut changements d'état playback
- [ ] Comparer zones avant/après action manuelle dans Roon
- [ ] Tester impact de réduire intervalle polling
- [ ] Analyser la structure complète de l'objet `data` dans callback

### Solutions Potentielles

#### Option 1: Polling Frontend Accéléré
```typescript
// Réduire à 1s pour actions utilisateur
const interval = setInterval(() => {
  fetchRoonStatus();
}, 1000); // Au lieu de 3000
```

**Avantage:** Synchronisation plus rapide  
**Inconvénient:** Plus de requêtes HTTP

#### Option 2: WebSocket Real-Time
```python
# Backend: SSE ou WebSocket
from fastapi import WebSocket

@router.websocket("/ws/roon")
async def roon_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Envoyer état en temps réel
        status = roon_service.get_now_playing()
        await websocket.send_json(status)
        await asyncio.sleep(0.5)
```

```typescript
// Frontend: Connexion WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/roon/ws/roon');
ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  setRoonStatus(status);
};
```

**Avantage:** Temps réel véritable  
**Inconvénient:** Complexité architecture

#### Option 3: Callback Enrichi
```python
def zones_callback(action, data):
    """Callback appelé pour TOUS les changements."""
    logger.info(f"🔔 Roon callback: action={action}")
    
    if action in ['zones_changed', 'zones_seek_changed']:
        roon_service.zones = roon_service.roon_api.zones
        # Notifier frontend via cache ou événement
        logger.info(f"🔄 État Roon mis à jour: {action}")
```

**Avantage:** Synchronisation événementielle  
**Inconvénient:** Dépend du comportement callback pyroon

#### Option 4: Force Refresh API
```python
def get_now_playing(self) -> dict:
    """Récupérer état actuel en forçant refresh."""
    # Forcer refresh depuis Roon API
    if hasattr(self.roon_api, 'zones'):
        self.zones = self.roon_api.zones  # Refresh direct
    
    if not self.default_zone_id or self.default_zone_id not in self.zones:
        return {"is_playing": False}
    
    # ... reste du code
```

### Workaround Actuel

**Utilisateur:**
- Rafraîchir manuellement la page (F5)
- Attendre le prochain cycle de polling (max 3-120s)
- Privilégier actions depuis AIME plutôt que Roon directement

---

## 📊 Logs de Debug Recommandés

### À ajouter dans `roon_service.py`:

```python
import logging
import time

logger = logging.getLogger(__name__)

def play(self) -> bool:
    """Démarrer la lecture avec logging détaillé."""
    logger.info(f"🎵 [PLAY] Command received - Zone: {self.default_zone_id}")
    
    if not self.default_zone_id:
        logger.warning("🎵 [PLAY] ❌ No default zone")
        return False
    
    # État avant
    zone_before = self.zones.get(self.default_zone_id, {})
    state_before = zone_before.get('state', 'unknown')
    logger.info(f"🎵 [PLAY] State before: {state_before}")
    
    # Commande
    start_time = time.time()
    try:
        self.roon_api.playback_control(self.default_zone_id, 'play')
        logger.info(f"🎵 [PLAY] ✅ Command sent to pyroon")
    except Exception as e:
        logger.error(f"🎵 [PLAY] ❌ Exception: {e}")
        return False
    
    # État après (avec retry)
    for i in range(5):
        time.sleep(0.2)
        zone_after = self.zones.get(self.default_zone_id, {})
        state_after = zone_after.get('state', 'unknown')
        elapsed = time.time() - start_time
        
        logger.info(f"🎵 [PLAY] Check {i+1}/5: {state_after} (elapsed: {elapsed:.2f}s)")
        
        if state_after == 'playing':
            logger.info(f"🎵 [PLAY] ✅ Success after {elapsed:.2f}s")
            return True
    
    logger.warning(f"🎵 [PLAY] ⚠️ State not confirmed playing after 1s")
    return False
```

### À ajouter dans `RoonContext.tsx`:

```typescript
const fetchRoonStatus = async () => {
  const startTime = Date.now();
  console.log('[ROON] 🔄 Fetching status...');
  
  try {
    const response = await axios.get('/api/v1/roon/now-playing');
    const elapsed = Date.now() - startTime;
    
    console.log(`[ROON] ✅ Status received (${elapsed}ms):`, response.data);
    setRoonStatus(response.data);
  } catch (error) {
    const elapsed = Date.now() - startTime;
    console.error(`[ROON] ❌ Error after ${elapsed}ms:`, error);
  }
};
```

---

## 🔬 Investigation en Cours

### Prochaines Étapes

1. **Semaine 1** (3-7 février):
   - [ ] Ajouter logs détaillés (voir section ci-dessus)
   - [ ] Collecter données sur 48h d'utilisation normale
   - [ ] Identifier patterns de défaillance

2. **Semaine 2** (10-14 février):
   - [ ] Analyser logs collectés
   - [ ] Tester solutions potentielles en local
   - [ ] Choisir meilleure approche

3. **Semaine 3** (17-21 février):
   - [ ] Implémenter solution choisie
   - [ ] Tests extensifs (unit + integration)
   - [ ] Documentation mise à jour

### Mesures de Success

- ✅ Commandes Play/Pause/Next fonctionnent 95%+ du temps
- ✅ Désynchronisation < 1 seconde
- ✅ Logs explicites sur causes d'échec
- ✅ Tests automatisés couvrant les cas d'erreur

---

## 📚 Ressources

- [pyroon Documentation](https://github.com/pavoni/pyroon)
- [Roon API](https://github.com/RoonLabs/node-roon-api)
- [ROON-INTEGRATION-COMPLETE.md](ROON-INTEGRATION-COMPLETE.md)
- [ROON-ZONES-FIX.md](ROON-ZONES-FIX.md)

---

**Dernière mise à jour:** 1er février 2026  
**Responsable:** Patrick Ostertag  
**Priorité:** 🔴 Haute
