# Post-Wake Recovery Optimization

## 🎯 Objectif

Assurer que le système redémarre rapidement et complètement après une mise en veille (sleep/wake).

## 🔍 Problèmes Identifiés

### Phase 3 - Tentative incorrecte
- **Symptôme**: Système figé lors de la sortie de veille
- **Diagnostic proposé**: `scheduler.start()` bloquerait la boucle d'événements
- **Solution proposée**: Envelopper avec `run_in_executor()` et `ThreadPoolExecutor`
- **Résultat ❌**: Les trackers se lançaient mais ne fonctionnaient pas réellement

### Phase 5 - Découverte
- **Vraie cause**: `AsyncIOScheduler.start()` n'est PAS bloquant
- `AsyncIOScheduler` est conçu pour les contextes async
- Envelopper avec executor brisait l'attachement à la boucle d'événements
- **Solution correcte**: Appels directs sans executor (beaucoup plus simple !)

### Vrai problème (probablement)
- Reconnexion à SQLite après wake-up (timeout ou verrouillage)
- Attente réseau pour les APIs externes (Last.fm, Roon, Spotify, etc.)
- Ceux-ci PEUVENT prendre du temps, mais n'interfèrent pas avec l'app startup

## ✅ Optimisations Actuelles

### 1. Lifespan Resilience (main.py)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB init (FATAL si échoue)
    try:
        init_db()
    except Exception as e:
        raise RuntimeError(...)
    
    # Service restore (NON-FATAL)
    try:
        await restore_active_services()
    except Exception as e:
        logger.warning("⚠️ Services non restaurés mais app démarre")
```

**Avantage**: L'application démarre même si les trackers/scheduler peuvent't reconnect immédiatement.

### 2. Enhanced Service Restoration (services.py)
```python
async def restore_active_services():
    restored_count = 0
    failed_count = 0
    
    for service in active_services:
        try:
            await service.start()
            restored_count += 1
        except Exception as e:
            logger.error(f"Service {name}: {e}", exc_info=True)
            failed_count += 1
            # Continue - don't block other services
    
    logger.info(f"📊 Résumé: {restored_count} succès, {failed_count} erreurs")
```

**Avantage**: 
- Les erreurs d'un service n'empêchent pas les autres de se lancer
- Logs détaillés avec tracebacks complets pour le debugging
- Compteurs pour visualiser l'état de recovery

### 3. Database Connection Optimization (database.py)
```python
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    # WAL mode: lecture/écriture simultanées
    dbapi_conn.execute("PRAGMA journal_mode = WAL")
    # Timeouts augmentés
    dbapi_conn.timeout = 30
    logger.debug("🔌 Connection configured for post-wake recovery")

@event.listens_for(engine, "engine_disposed")
def receive_engine_disposed(engine):
    logger.info("🔌 Reconnexion au prochain accès")
```

**Avantage**:
- WAL mode permet lecture pendant écriture
- Timeouts augmentés permettent au système de se stabiliser
- Logs de reconnexion pour diagnostiquer les problèmes

## 📊 Comportement Attendu

### Démarrage Normal (< 1s)
```
✅ Base de données initialisée
✅ Validation des composants OK
✅ Restauration des services
  ✅ Tracker Last.fm restauré
  ✅ Tracker Roon restauré
  ✅ Scheduler restauré
📊 Résumé: 3 succès, 0 erreurs
✅ Application ready
```

### Sortie de Veille avec Réseau Lent (2-5s)
```
✅ Base de données initialisée
✅ Validation des composants OK
✅ Restauration des services
  ❌ Tracker Roon: Connection timeout après 3s
  ✅ Tracker Last.fm restauré
  ✅ Scheduler restauré
📊 Résumé: 2 succès, 1 erreur
⚠️ Application démarrant sans Roon actif
✅ Application ready
```

L'app est prête à servir ~ immédiatement. Roon Tracker peut se reconnecter plus tard via heartbeat/health checks.

### Sortie de Veille avec DB Verrouillée (1-3s)
```
❌ Erreur initialisation BD: Database is locked
✅ (SQLite WAL mode relâche les verrous après ~1s)
✅ Base de données initialisée (retry)
...
```

## 🔧 Comment Tester

### 1. Configuration du système en veille
```bash
# macOS
pmset displaysleepnow

# Linux
systemctl suspend

# Windows
rundll32.exe powrprof.dll,SetSuspendState Sleep
```

### 2. Observer les logs
```bash
# Terminal 1: Logs
tail -f logs/app.log | grep -E "POST-WAKE|Restauration|Erreur"

# Terminal 2: Démarrage de l'app
uvicorn backend.app.main:app --reload
```

### 3. Vérifier la récupération
- [ ] API répond rapidement (< 1s après wake)
- [ ] Floating player affiche la piste active si elle jouait
- [ ] Zone de lecture est correctement restaurée
- [ ] Trackers commencent à enregistrer après reconnexion réseau
- [ ] Aucune exception non-loggée en console

## 📝 Logs à Observer

### ✅ Bon (Recovery complète < 2s)
```
🔄 Restauration des services actifs...
✅ Tracker Last.fm restauré
✅ Tracker Roon restauré
✅ Scheduler restauré
📊 Restauration complète: 3 succès, 0 erreurs
✅ Application ready to serve requests
```

### ⚠️ Acceptable (Recovery partielle)
```
🔄 Restauration des services actifs...
✅ Tracker Last.fm restauré
❌ Erreur restauration service 'roon_tracker': Connection timeout
✅ Scheduler restauré
📊 Restauration complète: 2 succès, 1 erreur
⚠️ Application démarrant sans services actifs
✅ Application ready to serve requests
```

### ❌ Problème (Recovery échouée)
```
❌ Erreur initialisation BD: Database is locked
❌ Erreur critique au démarrage: Database initialization failed
```
→ Investiguer si SQLite WAL mode est activé

## 🚀 Prochaines Optimisations

### 1. Connection Pool Refresh (HIGH)
```python
def reset_db_connections_for_wake():
    """Reset du pool après wake-up pour éviter les vieilles connexions."""
    engine.dispose()
    logger.info("🔄 Pool de connexions réinitialisé post-wake")
```

### 2. Service Retry Logic (MEDIUM)
```python
async def restore_with_retries(max_retries=3):
    """Retry service startup avec backoff exponentiel."""
    for service in services:
        wait_time = 1
        for attempt in range(max_retries):
            try:
                await service.start()
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                    wait_time *= 2
```

### 3. Health Check Heartbeat (MEDIUM)
```python
async def post_wake_health_checks():
    """Vérifier la santé après wake-up et relancer les services."""
    await asyncio.sleep(5)  # Attendre stabilisation
    
    for service in [tracker, roon_tracker, scheduler]:
        if not service.is_running:
            try:
                await service.start()
                logger.info(f"♻️ {service.name} relancé post-stabilisation")
            except Exception as e:
                logger.warning(f"Impossible de relancer {service.name}: {e}")
```

## 📚 Références

- [Tracker Init Issue Resolution](./TRACKER-INIT-ISSUE-RESOLUTION.md) - Apprentissages des Phases 3-5
- [Floating Player Auto-Show](./FLOATING-PLAYER-AUTO-SHOW.md) - UI recovery
- [System Architecture](../../../docs/architecture/SYSTEM-ARCHITECTURE.md)
