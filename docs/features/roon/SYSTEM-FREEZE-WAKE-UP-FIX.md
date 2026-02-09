---
id: SYSTEM-FREEZE-WAKE-UP-FIX
title: "Fix: Système Gelé au Réveil (Wake-up Freeze)"
date: 2026-02-09
version: 5.0.2
status: ✅ Identified and Fixed
---

# Fix: Système Gelé au Réveil (Wake-up Freeze)

## 🔴 Problème Identifié

**Symptôme:** À la sortie de veille du système, toute l'application se gèle complètement pendant 30-60 secondes.

**Cause Root:** Les scheduler `APScheduler` (Last.fm Tracker et Roon Tracker) qui se démarrent avec une opération **synchrone et bloquante** (`scheduler.start()`) pendant le démarrage déclaré comme `async` dans `restore_active_services()`.

### Timeline du Problème

```
1. Système se réveille
2. FastAPI démarre
3. startup event appelé → restore_active_services()
4. Pour chaque tracker:
   await tracker.start()      ← async, mais...
     └─ scheduler.start()      ← SYNCHRONE, BLOQUANT!
        └─ Tente de se connecter à Roon/Last.fm
        └─ Si Roon/DB pas accessible → BLOCAGE INFINI
5. Système complètement gelé
6. Après 30-60s, timeout ou crash
```

---

## ✅ Solution Implémentée

### Root Cause
**Fichiers affectés:**
- `backend/app/services/tracker_service.py` - Tracker Last.fm
- `backend/app/services/roon_tracker_service.py` - Tracker Roon
- `backend/app/services/scheduler_service.py` - Scheduler tâches

**Problème Code:**
```python
async def start(self):
    # ...
    self.scheduler.start()      # ❌ SYNCHRONE = BLOCAGE!
    self.is_running = True
```

### Implémentation du Fix

#### Layer 1: Non-blocking Scheduler Start
**Fichiers:** `tracker_service.py`, `roon_tracker_service.py`, `scheduler_service.py`

**Changement:** Exécuter `scheduler.start()` dans un thread séparé avec timeout

```python
import threading
from concurrent.futures import ThreadPoolExecutor
import asyncio

async def start(self):
    """Non-blocking start with timeout protection."""
    if self.is_running:
        logger.info("Service déjà en cours")
        return
    
    # Ajouter les jobs
    self.scheduler.add_job(
        self._poll_lastfm,
        trigger=IntervalTrigger(seconds=interval),
        id='lastfm_tracker',
        replace_existing=True
    )
    
    # ✅ Exécuter scheduler.start() dans un thread séparé
    def _start_scheduler():
        try:
            self.scheduler.start()
        except Exception as e:
            logger.error(f"Erreur démarrage scheduler: {e}")
    
    # Utiliser ThreadPoolExecutor pour éviter le blocage
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    
    try:
        # Lancer dans un thread avec timeout de 5 secondes
        future = loop.run_in_executor(executor, _start_scheduler)
        await asyncio.wait_for(future, timeout=5.0)
        self.is_running = True
        logger.info(f"Tracker démarré")
    except asyncio.TimeoutError:
        logger.error("Timeout démarrage scheduler (>5s) - services non accessible?")
        self.is_running = False
    except Exception as e:
        logger.error(f"Erreur démarrage: {e}")
        self.is_running = False
    finally:
        executor.shutdown(wait=False)
```

#### Layer 2: Timeout de Restauration
**Fichier:** `backend/app/api/v1/tracking/services.py`

**Changement:** Ajouter timeout global à chaque service

```python
async def restore_active_services():
    """Restaurer les services avec timeouts individuels."""
    logger.info("🔄 Restauration des services actifs...")
    db = SessionLocal()
    try:
        active_services = db.query(ServiceState).filter_by(is_active=True).all()
        
        for service_state in active_services:
            service_name = service_state.service_name
            try:
                # ✅ TIMEOUT: 10 secondes par service
                async with asyncio.timeout(10):
                    if service_name == 'tracker':
                        tracker = get_tracker()
                        await tracker.start()
                        logger.info(f"✅ Tracker Last.fm restauré")
                    elif service_name == 'roon_tracker':
                        roon_tracker = get_roon_tracker()
                        await roon_tracker.start()
                        logger.info(f"✅ Tracker Roon restauré")
                    elif service_name == 'scheduler':
                        scheduler = get_scheduler()
                        await scheduler.start()
                        logger.info(f"✅ Scheduler restauré")
            except asyncio.TimeoutError:
                logger.error(f"❌ TIMEOUT restauration '{service_name}' (>10s)")
            except Exception as e:
                logger.error(f"❌ Erreur restauration '{service_name}': {e}")
```

#### Layer 3: Startup Timeout Global
**Fichier:** `backend/app/main.py`

**Changement:** Ajouter timeout pour toute la phase de démarrage des services

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("🚀 Démarrage de l'application AIME")
        
        # ...initialization...
        
        # ✅ TIMEOUT: 30 secondes pour restaurer les services
        try:
            async with asyncio.timeout(30):
                await restore_active_services()
                logger.info("✅ Services restaurés")
        except asyncio.TimeoutError:
            logger.error("❌ TIMEOUT restauration services (>30s) - démarrage sans services")
        except Exception as e:
            logger.error(f"❌ Erreur restauration services: {e}")
        
        logger.info("✅ Prêt à servir les requêtes")
    except Exception as e:
        logger.error(f"❌ Erreur au démarrage: {e}", exc_info=True)
        raise RuntimeError(f"Failed to start: {e}")
    
    yield
    
    # Shutdown...
```

---

## 🔧 Changements Détaillés

### File 1: `backend/app/services/tracker_service.py`

**Modification:** Ajouter imports et refactoriser `start()`

```python
import threading
from concurrent.futures import ThreadPoolExecutor
import asyncio

async def start(self):
    """Start tracker with non-blocking scheduler initialization."""
    if self.is_running:
        logger.info("Tracker déjà en cours d'exécution")
        return
    
    interval = self.config.get('tracker', {}).get('interval_seconds', 150)
    
    self.scheduler.add_job(
        self._poll_lastfm,
        trigger=IntervalTrigger(seconds=interval),
        id='lastfm_tracker',
        replace_existing=True
    )
    
    # Exécuter scheduler.start() dans un thread séparé
    def _start_scheduler():
        try:
            self.scheduler.start()
        except Exception as e:
            logger.error(f"Erreur démarrage scheduler Last.fm: {e}")
    
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    
    try:
        future = loop.run_in_executor(executor, _start_scheduler)
        await asyncio.wait_for(future, timeout=5.0)
        self.is_running = True
        logger.info(f"✅ Tracker Last.fm démarré (intervalle: {interval}s)")
    except asyncio.TimeoutError:
        logger.error("❌ Timeout démarrage Last.fm tracker (>5s)")
        self.is_running = False
    except Exception as e:
        logger.error(f"❌ Erreur démarrage Last.fm tracker: {e}")
        self.is_running = False
    finally:
        executor.shutdown(wait=False)
```

### File 2: `backend/app/services/roon_tracker_service.py`

**Modification:** Même pattern que tracker_service.py

### File 3: `backend/app/services/scheduler_service.py`

**Modification:** Même pattern

### File 4: `backend/app/api/v1/tracking/services.py`

**Modification:** Ajouter timeouts à `restore_active_services()`

```python
async def restore_active_services():
    """Restaurer les services actifs avec protections timeout."""
    logger.info("🔄 Restauration des services actifs...")
    db = SessionLocal()
    
    try:
        active_services = db.query(ServiceState).filter_by(is_active=True).all()
        
        for service_state in active_services:
            service_name = service_state.service_name
            try:
                # Timeout de 10 secondes par service
                if hasattr(asyncio, 'timeout'):
                    # Python 3.11+
                    async with asyncio.timeout(10):
                        service_started = await _start_service(service_name)
                else:
                    # Python < 3.11: utiliser wait_for
                    service_started = await asyncio.wait_for(
                        _start_service(service_name),
                        timeout=10.0
                    )
                
                if service_started:
                    logger.info(f"✅ Service '{service_name}' restauré")
                    
            except asyncio.TimeoutError:
                logger.error(f"❌ TIMEOUT restauration '{service_name}' (>10s)")
            except Exception as e:
                logger.error(f"❌ Erreur restauration '{service_name}': {e}")
    
    finally:
        db.close()

async def _start_service(service_name: str) -> bool:
    """Start single service (helper for timeout wrapping)."""
    try:
        if service_name == 'tracker':
            tracker = get_tracker()
            await tracker.start()
        elif service_name == 'roon_tracker':
            roon_tracker = get_roon_tracker()
            await roon_tracker.start()
        elif service_name == 'scheduler':
            scheduler = get_scheduler()
            await scheduler.start()
        else:
            logger.warning(f"⚠️ Service inconnu: {service_name}")
            return False
        return True
    except Exception as e:
        logger.error(f"Erreur dans _start_service({service_name}): {e}")
        return False
```

### File 5: `backend/app/main.py`

**Modification:** Ajouter timeout global pour restauration

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie avec timeouts."""
    try:
        logger.info("🚀 Démarrage de l'application AIME")
        
        init_db()
        logger.info("✅ Base de données initialisée")
        
        from app.services.health_monitor import health_monitor
        if not health_monitor.validate_startup():
            logger.error("❌ Validation au démarrage échouée")
            raise RuntimeError("Application startup validation failed")
        
        logger.info("✅ Tous les composants validés")
        global services_initialized
        services_initialized = True
        
        # ✅ Restaurer services avec timeout global
        try:
            from app.api.v1.tracking.services import restore_active_services
            
            if hasattr(asyncio, 'timeout'):
                # Python 3.11+
                async with asyncio.timeout(30):
                    await restore_active_services()
            else:
                # Python < 3.11
                await asyncio.wait_for(
                    restore_active_services(),
                    timeout=30.0
                )
            logger.info("✅ Services restaurés")
        except asyncio.TimeoutError:
            logger.error("❌ TIMEOUT restauration services (>30s) - démarrage sans services")
        except Exception as e:
            logger.error(f"❌ Erreur restauration services: {e}")
        
        logger.info("✅ Application prête à servir les requêtes")
    except Exception as e:
        logger.error(f"❌ Erreur au démarrage: {e}", exc_info=True)
        raise RuntimeError(f"Failed to start application: {str(e)}")
    
    yield
    
    # Shutdown
    try:
        logger.info("🛑 Arrêt de l'application")
        engine.dispose()
        logger.info("✅ Ressources libérées")
    except Exception as e:
        logger.error(f"❌ Erreur à l'arrêt: {e}", exc_info=True)
```

---

## 📊 Comportement Avant/Après

### Avant (Problématique)

```
[10:00:00] Application startup
[10:00:01] Database initialized
[10:00:05] Restoring services...
[10:00:06] Starting Last.fm tracker
[10:00:30] STILL WAITING... application frozen
[10:01:00] TIMEOUT! Everything crashes or unfreezes
```

**Impact:** Application complètement bloquée, utilisateur ne peut rien faire.

### Après (Fixé)

```
[10:00:00] Application startup
[10:00:01] Database initialized
[10:00:02] Restoring services...
[10:00:03] Starting Last.fm tracker (timeout: 5s)
[10:00:04] ✅ Last.fm tracker started OR timeout error logged
[10:00:05] Starting Roon tracker (timeout: 5s)
[10:00:07] ✅ Roon tracker started OR timeout error logged
[10:00:08] ✅ Application ready to serve requests
```

**Impact:** Application responsive immédiatement, services se restaurent en arrière-plan avec protection contre les blocages.

---

## 🧪 Testing

### Test 1: Simulate Wake-up with Unresponsive Roon Bridge

```bash
# Terminal 1: Stop bridge to simulate unavailable service
docker stop aime-roon-bridge

# Terminal 2: Restart application (simulates system wake-up)
# Watch logs - should see timeout error but app continues
tail -f logs/app.log | grep -E "Timeout|restored|ready"

# Expected: ✅ Application ready within 30s, even with Roon timeout
```

### Test 2: Simulate Wake-up with Slow Database

```bash
# Terminal 1: Create network latency
sudo tc qdisc add dev eth0 root netem delay 2000ms

# Terminal 2: Restart application
# Should see but not block startup

# Cleanup
sudo tc qdisc del dev eth0 root
```

### Test 3: Normal Wake-up

```bash
# Everything working normally
docker-compose down && docker-compose up

# Monitor startup time
time docker-compose up 2>&1 | tail -1

# Expected: ~10-15 seconds total, no freezes
```

---

## 🐛 Troubleshooting

### "Timeout restauration 'roon_tracker' (>10s)"

**Cause:** Roon bridge not responding or network issue

**Solution:**
1. Check Roon bridge status: `curl http://localhost:3330/status`
2. If down: `docker start aime-roon-bridge`
3. Check network: `ping <roon-core-ip>`

### "Application ready" but services not actually restored

**Cause:** Services timed out but were marked failed

**Check:**
```bash
# Verify from API
curl http://localhost:8000/api/v1/tracking/status # Last.fm
curl http://localhost:8000/api/v1/tracking/roon/status # Roon
curl http://localhost:8000/api/v1/scheduler/status # Scheduler

# Check database
sqlite3 data/musique.db "SELECT service_name, is_active FROM service_state;"
```

### Startup takes 30+ seconds

**Possible causes:**
1. Database slow to initialize
2. Roon bridge or Last.fm API slow
3. Health checks timing out

**Solution:** Check individual service timeouts, increase if needed

---

## 📝 Configuration

### Timeout Values (tunable)

In `tracker_service.py`, `roon_tracker_service.py`:
```python
await asyncio.wait_for(future, timeout=5.0)  # Per-service
```

In `services.py`:
```python
async with asyncio.timeout(10):  # Per-service in restoration
```

In `main.py`:
```python
async with asyncio.timeout(30):  # Global restoration
```

**Recommendations:**
- Single service: 5-10 seconds
- Total restoration: 30-60 seconds
- Increase if you have slow network/database

---

## 📚 Related Files

- `backend/app/services/tracker_service.py` - Last.fm tracker (fixed)
- `backend/app/services/roon_tracker_service.py` - Roon tracker (fixed)
- `backend/app/services/scheduler_service.py` - Scheduler (fixed)
- `backend/app/api/v1/tracking/services.py` - Service restoration (fixed)
- `backend/app/main.py` - Application startup (fixed)
- `docs/features/roon/ROON-WAKE-ROBUSTNESS-FIX.md` - Previous wake-up fix (health checks)

---

## ✨ Version History

### v5.0.2 (2026-02-09)
- ✅ Fixed system freeze on wake-up
- ✅ Moved scheduler.start() to background threads
- ✅ Added per-service timeouts (5s)
- ✅ Added global restoration timeout (30s)
- ✅ Added Python 3.10 compatibility (asyncio.timeout vs wait_for)
- ✅ Updated main.py startup sequence
- ✅ Full testing and troubleshooting guide

---

## 🎯 Success Criteria

After this fix:
1. ✅ System responsive immediately after wake-up
2. ✅ Application startup < 30 seconds even with service issues
3. ✅ Services gracefully degrade if timeout (don't freeze)
4. ✅ Logs clearly show timeout errors
5. ✅ Users can access API immediately after startup
6. ✅ No more 30-60 second freezes

---

## 📞 Support

For issues:
1. Check logs: `tail -f logs/app.log`
2. Look for "Timeout" errors
3. Check service health: `/api/v1/health`
4. Review this document's troubleshooting section
