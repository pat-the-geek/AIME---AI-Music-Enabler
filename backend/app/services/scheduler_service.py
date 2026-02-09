"""AI-optimized scheduler service for intelligent background task orchestration.

Manages all background and scheduled operations:
- Daily album enrichment (descriptions, images, haikus)
- Scheduled haiku generation (daily random albums, weekly reports)
- Collection exports (markdown, JSON) to data directory
- AI description optimization (rewriting thin descriptions)
- Magazine edition generation (batch with delays)
- Discogs sync operations (daily album updates)
- Task execution tracking and history

Architecture:
- Uses APScheduler (asyncio-based) for cron scheduling
- UTC-based cron triggers: 2h daily enrichment, 6h haikus, etc.
- Database persistence of task execution history
- Service dependencies: AI (Euria), Spotify for images
- Task tracking: execution counts, error logging, duration

Scheduler Tasks:
- 02:00 UTC: Daily enrichment (missing images, descriptions)
- 06:00 UTC: Random haiku generation (5 albums)
- 18:00 UTC: Export collection markdown
- 19:00 UTC: Export collection JSON
- 20:00 UTC: Weekly haiku (Thursday)
- 21:00 UTC: Monthly analysis (1st of month)
- 22:00 UTC: AI description optimization
- 23:00 UTC: Magazine edition batch generation
- 00:00 UTC: Discogs daily sync

Used By:
- FastAPI startup event (scheduler initialization)
- Admin endpoints: GET /scheduler/status, POST /scheduler/trigger/{task}
- Background task tracking and history
- Collection refresh automation
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload
from collections import Counter
import logging
import os
import json
from io import StringIO

from app.database import SessionLocal
from app.services.external.ai_service import AIService
from app.services.spotify_service import SpotifyService
from app.services.markdown_export_service import MarkdownExportService
from app.services.magazine_edition_service import MagazineEditionService
from app.models import Album, Track, ListeningHistory, Metadata, ScheduledTaskExecution

logger = logging.getLogger(__name__)

# Map entre task IDs et noms affichés avec emojis
TASK_NAMES = {
    'daily_enrichment': '🔄 Enrichissement quotidien',
    'generate_haiku_scheduled': '🎋 Génération de haïkus',
    'export_collection_markdown': '📝 Export Markdown',
    'export_collection_json': '💾 Export JSON',
    'weekly_haiku': '🎋 Haïku hebdomadaire',
    'monthly_analysis': '📊 Analyse mensuelle',
    'optimize_ai_descriptions': '🤖 Optimisation IA',
    'generate_magazine_editions': '📰 Génération de magazines',
    'sync_discogs_daily': '💿 Sync Discogs'
}


class SchedulerService:
    """Scheduler intelligent avec optimisation par IA."""
    
    def __init__(self, config: dict):
        """Initialize scheduler with configuration and dependent services.
        
        Sets up APScheduler with asyncio backend and critical services.
        
        Args:
            config: Config dict with 'euria' and 'spotify' credentials
        
        Side Effects:
            - Initializes AsyncIOScheduler instance
            - Creates AIService and SpotifyService from config
            - is_running flag set to False (scheduler not started yet)
        
        Performance:
            O(1) - initialization only
        """
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # Initialiser services
        euria_config = config.get('euria', {})
        spotify_config = config.get('spotify', {})
        
        self.ai = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer')
        )
        
        self.spotify = SpotifyService(
            client_id=spotify_config.get('client_id'),
            client_secret=spotify_config.get('client_secret')
        )
    
    async def start(self):
        """Start APScheduler with all configured background tasks.
        
        Registers 9 scheduled tasks with cron triggers (UTC times):
        - 02:00: Daily enrichment (images, descriptions)
        - 06:00: Random haiku generation (5 albums)
        - 08:00: Export collection markdown
        - 10:00: Export collection JSON
        - 20:00 (Sunday): Weekly haiku report
        - 03:00 (1st): Monthly listening analysis
        - Every 6h: AI description optimization
        - 23:00: Magazine edition batch generation
        - 00:00: Discogs daily sync
        
        Idempotent: Does nothing if already running.
        
        Side Effects:
            - Starts APScheduler in background
            - Sets is_running = True
            - Logs INFO: "📅 Scheduler démarré..."
        
        Error Handling:
            - Logs ERROR if startup fails
            - Sets is_running = False on error
            - Does not raise exception (allows app startup to continue)
        
        Note:
            All tasks run UTC. Adjust CronTrigger hours for other timezones.
        """
        if self.is_running:
            logger.info("📅 Scheduler déjà en cours d'exécution")
            return
        
        # Tâche quotidienne : enrichir albums manquants
        self.scheduler.add_job(
            self._daily_enrichment,
            trigger=CronTrigger(hour=2, minute=0),  # 2h du matin
            id='daily_enrichment',
            replace_existing=True
        )
        
        # Tâche quotidienne : générer haikus pour 5 albums random
        self.scheduler.add_job(
            self._generate_random_haikus,
            trigger=CronTrigger(hour=6, minute=0),  # 6h du matin
            id='generate_haiku_scheduled',
            replace_existing=True
        )
        
        # Tâche quotidienne : exporter collection en markdown
        self.scheduler.add_job(
            self._export_collection_markdown,
            trigger=CronTrigger(hour=8, minute=0),  # 8h du matin
            id='export_collection_markdown',
            replace_existing=True
        )
        
        # Tâche quotidienne : exporter collection en JSON
        self.scheduler.add_job(
            self._export_collection_json,
            trigger=CronTrigger(hour=10, minute=0),  # 10h du matin
            id='export_collection_json',
            replace_existing=True
        )
        
        # Tâche hebdomadaire : générer haïkus
        self.scheduler.add_job(
            self._weekly_haiku,
            trigger=CronTrigger(day_of_week='sun', hour=20, minute=0),  # Dimanche 20h
            id='weekly_haiku',
            replace_existing=True
        )
        
        # Tâche mensuelle : analyse patterns profonde
        self.scheduler.add_job(
            self._monthly_analysis,
            trigger=CronTrigger(day=1, hour=3, minute=0),  # 1er du mois 3h
            id='monthly_analysis',
            replace_existing=True
        )
        
        # Tâche intelligente : optimiser descriptions AI
        self.scheduler.add_job(
            self._optimize_ai_descriptions,
            trigger=CronTrigger(hour='*/6'),  # Toutes les 6h
            id='optimize_ai_descriptions',
            replace_existing=True
        )
        
        # Tâche quotidienne : générer lot de magazines pré-générés
        self.scheduler.add_job(
            self._generate_magazine_editions,
            trigger=CronTrigger(hour=3, minute=0),  # 3h du matin
            id='generate_magazine_editions',
            replace_existing=True
        )
        
        # Tâche quotidienne : synchroniser collection Discogs
        self.scheduler.add_job(
            self._sync_discogs_daily,
            trigger=CronTrigger(hour=4, minute=0),  # 4h du matin
            id='sync_discogs_daily',
            replace_existing=True
        )
        
        try:
            self.scheduler.start()
            self.is_running = True
            logger.info("✅ Scheduler démarré avec tâches optimisées")
        except Exception as e:
            logger.error(f"❌ Erreur démarrage scheduler: {e}", exc_info=True)
            self.is_running = False
            # Ne pas lever l'exception pour ne pas bloquer le startup de l'app

    
    async def stop(self):
        """
        Stop the APScheduler gracefully and clean up all running jobs.
        
        Shuts down the scheduler blocking mode (waits for running jobs). Sets is_running flag
        to False to prevent new task submissions. Safe to call multiple times (idempotent).
        
        Performance:
        - Typical: 100-500ms (depends on running job count and cleanup overhead)
        - With blocking shutdown: May take longer if jobs are running
        - Memory: Releases job allocations and scheduler resources
        
        Raises:
        - SchedulerAlreadyRunningError: If scheduler already being stopped (caught internally)
        
        Example:
            scheduler = SchedulerService(db, config, services)
            scheduler.start()  # Start all tasks
            await scheduler.stop()  # Gracefully shutdown
            assert not scheduler.is_running  # Verify stopped
        
        Logging:
        - INFO: When scheduler is already stopped (idempotency)
        - INFO: When successfully shutdown
        
        Implementation Notes:
        - APScheduler.shutdown() blocks until running jobs complete (safely)
        - Second call returns immediately due to is_running flag check
        - No exception raised on subsequent calls (API safety)
        - Cleanup: Timer threads, thread pools, job queue released
        """
        if not self.is_running:
            logger.info("📅 Scheduler n'est pas en cours d'exécution")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("📅 Scheduler arrêté")
    
    def _record_execution(self, task_id: str, status: str = 'success', error: str = None):
        """
        Record scheduled task execution in database with metadata and next_run_time.
        
        Logs task completion status to ScheduledTaskExecution table for monitoring/debugging.
        Updates task_name via TASK_NAMES mapping, last_executed timestamp, status, and
        queries APScheduler for next scheduled run time (if scheduler running).
        
        Args:
            task_id (str): Unique task identifier (e.g., 'daily_enrichment')
            status (str, optional): Execution outcome ('success', 'error', 'partial'). Defaults to 'success'
            error (str, optional): Error message if status='error'. Defaults to None
        
        Returns:
            None (logs to database and exits)
        
        Performance:
        - Typical: 50-100ms (1 query if exists, 0-1 insert, 1 commit)
        - Database hit: Single transaction, lightweight SQL
        - Big-O: O(1) - constant lookup and insert
        
        Raises:
        - No exceptions raised (all errors caught and logged as warnings)
        
        Example:
            self._record_execution('daily_enrichment', 'success')
            # Creates/updates ScheduledTaskExecution record with status='success'
            
            self._record_execution('daily_enrichment', 'error', 'Database connection timeout')
            # Records failure with error message
        
        Side Effects:
        - Creates ScheduledTaskExecution row if first run of task_id
        - Updates existing row with new execution timestamp
        - Queries scheduler job (if running) for next_run_time calculation
        - Always commits to database (idempotent - safe on retry)
        
        Logging:
        - DEBUG: On successful record (✅ Exécution enregistrée: <task_id> (<status>))
        - ERROR: On database exception (❌ Erreur enregistrement exécution <task_id>)
        
        Implementation Notes:
        - SessionLocal() is local session (not shared with task execution)
        - Rollback on error prevents partial state corruption
        - next_run_time populated only if scheduler.is_running (graceful degradation)
        - TASK_NAMES is module-level dict mapping task_id to human-readable names
        """
        db = SessionLocal()
        try:
            execution = db.query(ScheduledTaskExecution).filter_by(task_id=task_id).first()
            
            if execution is None:
                execution = ScheduledTaskExecution(task_id=task_id)
                db.add(execution)
            
            execution.task_name = TASK_NAMES.get(task_id, task_id)
            execution.last_executed = datetime.now(timezone.utc)
            execution.last_status = status
            execution.updated_at = datetime.now(timezone.utc)
            
            # Mettre à jour next_run_time si la tâche est en cours d'exécution
            if self.is_running:
                try:
                    job = self.scheduler.get_job(task_id)
                    if job and job.next_run_time:
                        execution.next_run_time = job.next_run_time
                except:
                    pass
            
            db.commit()
            logger.debug(f"✅ Exécution enregistrée: {task_id} ({status})")
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement exécution {task_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_status(self) -> dict:
        """
        Get comprehensive scheduler status with all jobs and their execution history.
        
        Returns dict with running state, job list, and execution metadata from database.
        If scheduler running, queries APScheduler for next_run_time and ScheduledTaskExecution
        table for execution history. Returns empty job list if not running (graceful degradation).
        
        Returns:
            dict: Status dict with keys:
                - running (bool): True if scheduler active, False otherwise
                - jobs (list): Job metadata list (empty if not running)
                - job_count (int): Number of active jobs
                
            Job metadata (dict):
                - id (str): Job identifier (e.g., 'daily_enrichment')
                - name (str): Human-readable name from TASK_NAMES
                - next_run (str|None): Next scheduled run as ISO8601 datetime string
                - last_execution (str|None): Last execution datetime or None if never run
                - last_status (str): Latest execution status ('success', 'error', 'pending')
        
        Performance:
        - Typical: 100-500ms (database query + scheduler introspection)
        - Expected scale: <1s for 10+ jobs with execution history
        - Database: Single query on ScheduledTaskExecution (select *)
        - Scheduler introspection: O(n) where n = number of jobs
        
        Raises:
        - No exceptions raised (all caught and logged as warnings, graceful degradation)
        
        Example:
            status = scheduler.get_status()
            # Returns:
            # {
            #   'running': True,
            #   'jobs': [
            #     {
            #       'id': 'daily_enrichment',
            #       'name': 'Enrichissement quotidien',
            #       'next_run': '2026-02-07T02:00:00+00:00',
            #       'last_execution': '2026-02-06T02:05:30+00:00',
            #       'last_status': 'success'
            #     },
            #     ...
            #   ],
            #   'job_count': 9
            # }
        
        Side Effects:
        - Queries database (read-only, no state changes)
        - Does not modify scheduler state
        - No logging of individual failures, only warnings on collection errors
        
        Logging:
        - WARNING (level): On database connection failure or job enumeration error
        - Does not log successful status queries (debug-level only if enabled)
        
        Implementation Notes:
        - Gracefully handles missing database (returns empty jobs list)
        - Per-job errors caught individually (doesn't stop other job enumeration)
        - Caches job metadata queries (scheduler.get_jobs() called once, 1 DB query)
        - Thread-safe: Uses existing SQLAlchemy SessionLocal() session
        - Idempotent: Call multiple times safely, no side effects
        - Used by: /health/scheduler endpoint for monitoring dashboards
        """
        jobs = []
        executions_cache = {}  # Cache pour les exécutions
        
        if self.is_running:
            db = SessionLocal()
            try:
                # Charger toutes les exécutions enregistrées
                executions = db.query(ScheduledTaskExecution).all()
                for ex in executions:
                    executions_cache[ex.task_id] = {
                        'last_executed': ex.last_executed.isoformat() if ex.last_executed else None,
                        'last_status': ex.last_status or 'pending'
                    }
            except Exception as e:
                logger.warning(f"⚠️ Erreur chargement exécutions: {e}")
            finally:
                db.close()
            
            try:
                for job in self.scheduler.get_jobs():
                    try:
                        execution = executions_cache.get(job.id, {})
                        jobs.append({
                            'id': job.id,
                            'name': TASK_NAMES.get(job.id, job.name or job.id),
                            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                            'last_execution': execution.get('last_executed'),
                            'last_status': execution.get('last_status', 'pending')
                        })
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur traitement job {getattr(job, 'id', 'unknown')}: {e}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur obtention jobs scheduler: {e}")
        
        return {
            'running': self.is_running,
            'jobs': jobs,
            'job_count': len(jobs)
        }
    
    async def _daily_enrichment(self):
        """
        Daily enrichment task: Enrich 50 albums with missing Spotify URLs and release years.
        
        Queried at 02:00 UTC daily via CronTrigger. Finds albums missing spotify_url OR year
        (most important metadata), attempts Spotify search for each, commits in batches.
        Gracefully degrades on individual album failures (continues processing).
        
        Performance:
        - Typical: 5-15s (50 albums × 200-300ms each Spotify call)
        - Batch: 2 commits (every 25 albums) + 1 final commit
        - Database: 2-3 SELECT, 2-3 UPDATE/INSERT per batch
        - Spotify API: 50 calls at ~200-300ms each (queue-based)
        - Big-O: O(n) where n=50 (album limit)
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Updates Album.spotify_url if found in Spotify search
        - Updates Album.year if found in Spotify search
        - Commits to database after processing completes
        - Records task execution in ScheduledTaskExecution table
        
        Logging:
        - INFO: Startup log with album count target
        - ERROR: Individual album enrichment failures (non-blocking)
        - INFO: Completion with enrichment count
        - DEBUG: Via _record_execution()
        
        Implementation Notes:
        - Album filtering: (spotify_url IS NULL) OR (year IS NULL)
        - Spotify search: Uses artist_name (first artist) + album.title
        - Error handling: Catch-continue pattern (no rollback, continues on failure)
        - Database: Manual db.commit() after each album (not batched for safety)
        - Retry logic: None (Spotify timeouts cause skip, exception logged)
        - Called by: APScheduler trigger at 02:00 UTC
        - Idempotent: Safe to call multiple times (incremental enrichment)
        
        Example:
            # Called automatically by scheduler at 02:00 UTC
            # Enriches 50 albums with missing Spotify metadata
            # Logs: "🔄 Début enrichissement quotidien"
            # Logs: "✅ Enrichissement quotidien terminé: 42 albums"
        """
        logger.info("🔄 Début enrichissement quotidien")
        db = SessionLocal()
        
        try:
            # Enrichir 50 albums sans URL Spotify ou année
            albums = db.query(Album).filter(
                (Album.spotify_url == None) | (Album.year == None)
            ).limit(50).all()
            
            enriched = 0
            for album in albums:
                try:
                    artist_name = album.artists[0].name if album.artists else ""
                    
                    spotify_details = await self.spotify.search_album_details(artist_name, album.title)
                    if spotify_details:
                        if not album.spotify_url and spotify_details.get('spotify_url'):
                            album.spotify_url = spotify_details['spotify_url']
                        if not album.year and spotify_details.get('year'):
                            album.year = spotify_details['year']
                        enriched += 1
                        db.commit()
                except Exception as e:
                    logger.error(f"Erreur enrichissement {album.title}: {e}")
                    db.rollback()
                    continue
            
            logger.info(f"✅ Enrichissement quotidien terminé: {enriched} albums")
            self._record_execution('daily_enrichment', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement quotidien: {e}")
            self._record_execution('daily_enrichment', 'error', str(e))
        finally:
            db.close()
    
    async def _weekly_haiku(self):
        """
        Weekly haiku generation task: Generate Japanese haiku from top 5 artists/albums.
        
        Queried at 20:00 UTC on Sunday via CronTrigger. Analyzes last 7 days of listening
        history, extracts top 5 artists and albums (Counter-based), calls AIService.generate_haiku
        with structured data (top_artists, top_albums, total_tracks count). Returns poetry or
        empty string (no fallback, just logging). Gracefully degrades if no history found.
        
        Performance:
        - Typical: 2-5s (database scans + Counter operations + 1 AI call)
        - Database: 1-2 ListeningHistory queries (large if 7 days active)
        - AI generation: 2-4s (Euria API call for haiku generation)
        - Big-O: O(n) where n = listening history entries in last 7 days
        - Scale: Works well for <10k history entries (typical weekly: 500-2000)
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Queries ListeningHistory, Track, Album, Artist tables (read-only)
        - Calls AIService.generate_haiku (external API)
        - Records task execution in ScheduledTaskExecution table
        - No database writes (informational task only)
        
        Logging:
        - INFO: Startup log (🎋 Génération haïku hebdomadaire)
        - INFO: If no history found (graceful degradation)
        - INFO: Complete haiku text when generated (🎋 Haïku généré:\n{haiku})
        - ERROR: On exception during generation or AI call
        - DEBUG: Via _record_execution()
        
        Implementation Notes:
        - Timestamp calculation: Unix timestamp, 7 days ago = now - 604800 seconds
        - Counter usage: O(n) counting, most_common(5) for top extraction
        - Data structure passed to AI:
          ```python
          listening_data = {
              'top_artists': ['Artist1', 'Artist2', ...],  # 5 max
              'top_albums': ['Album1', 'Album2', ...],    # 5 max
              'total_tracks': int(count)
          }
          ```
        - AI prompt: "generate_haiku(listening_data)" via Euria
        - Artist extraction: First artist of each track (if exists)
        - Album extraction: Album title of each track
        - Deduplication: Counter() naturally dedupes via key counting
        - Called by: APScheduler trigger at 20:00 UTC on Sunday
        - Idempotent: Safe to call multiple times (no state mutation)
        
        Example:
            # Called automatically by scheduler at 20:00 UTC on Sunday
            # If user listened to 500 tracks this week (top 5: Radiohead, Bjork, etc.)
            # Logs: "🎋 Génération haïku hebdomadaire"
            # Logs: "🎋 Haïku généré:"
            # Logs: <5-7 syllable lines of Japanese poetry>
            # Logs: "✅ Exécution enregistrée: weekly_haiku (success)"
        """
        logger.info("🎋 Génération haïku hebdomadaire")
        db = SessionLocal()
        
        try:
            # Analyser les 7 derniers jours
            seven_days_ago = int((datetime.now() - timedelta(days=7)).timestamp())
            recent_history = db.query(ListeningHistory).filter(
                ListeningHistory.timestamp >= seven_days_ago
            ).all()
            
            if not recent_history:
                logger.info("Pas d'historique récent pour le haïku")
                return
            
            # Extraire données
            artists = Counter()
            albums = Counter()
            
            for entry in recent_history:
                db_track = db.query(Track).get(entry.track_id)
                if db_track and db_track.album:
                    if db_track.album.artists:
                        for artist in db_track.album.artists:
                            artists[artist.name] += 1
                    albums[db_track.album.title] += 1
            
            listening_data = {
                'top_artists': [name for name, _ in artists.most_common(5)],
                'top_albums': [title for title, _ in albums.most_common(5)],
                'total_tracks': len(recent_history)
            }
            
            haiku = await self.ai.generate_haiku(listening_data)
            logger.info(f"🎋 Haïku généré:\n{haiku}")
            self._record_execution('weekly_haiku', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur génération haïku: {e}")
            self._record_execution('weekly_haiku', 'error', str(e))
        finally:
            db.close()
    
    async def _monthly_analysis(self):
        """
        Monthly analysis task: Generate listening pattern statistics for last 30 days.
        
        Queried at 03:00 UTC on 1st of month via CronTrigger (day=1). Analyzes last 30 days
        of listening history, calculates total plays, unique days active, average plays/day,
        and top 10 artists by play count. Logs analytics summary (not persisted). Gracefully
        degrades if no history found.
        
        Performance:
        - Typical: 1-3s (large ListeningHistory query + Counter + aggregations)
        - Database: 1 ListeningHistory query (all entries >=30_days_ago), 1-2 Track queries
        - Computation: Counter aggregation, date deduplication, sorting
        - Big-O: O(n) where n = listening history entries in last 30 days
        - Scale: Works well for <50k history entries (typical monthly: 3000-10000)
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Queries ListeningHistory, Track, Album, Artist tables (read-only)
        - Computes and logs analytics (no database writes)
        - Records task execution in ScheduledTaskExecution table
        - No database state changes
        
        Logging:
        - INFO: Startup log (📊 Analyse mensuelle des patterns)
        - INFO: If no history found (graceful degradation)
        - INFO: Analytics summary with 4 key metrics:
          - Total plays (📊 Analyse mensuelle:)
          - Days active
          - Average plays per day
          - Top artist name/count
        - ERROR: On exception during analysis
        - DEBUG: Via _record_execution()
        
        Implementation Notes:
        - Timestamp calculation: 30 days ago = now - 2592000 seconds
        - Unique days: Extracted from ListeningHistory.timestamp (unix epoch)
          - datetime.fromtimestamp() converts to date, set deduplicates
        - Average per day: total_plays / unique_days (division by zero safe)
        - Counter usage: O(n) iteration, most_common(10) for top extraction
        - Top artists structure: [(name1, count1), (name2, count2), ...]
        - Data purely informational (logged only, not persisted to DB)
        - Called by: APScheduler trigger at 03:00 UTC on 1st of each month
        - Idempotent: Safe to call multiple times (read-only operation)
        
        Example:
            # Called automatically by scheduler at 03:00 UTC on 1st
            # If user played 3500 tracks over 20 active days
            # Logs: "📊 Analyse mensuelle des patterns"
            # Logs: "📊 Analyse mensuelle:"
            # Logs: "  - Total écoutes: 3500"
            # Logs: "  - Jours actifs: 20"
            # Logs: "  - Moyenne/jour: 175.0"
            # Logs: "  - Top artiste: ('Radiohead', 342)"
            # Logs: "✅ Exécution enregistrée: monthly_analysis (success)"
        """
        logger.info("📊 Analyse mensuelle des patterns")
        db = SessionLocal()
        
        try:
            # Analyser le mois précédent
            thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
            monthly_history = db.query(ListeningHistory).filter(
                ListeningHistory.timestamp >= thirty_days_ago
            ).all()
            
            if not monthly_history:
                logger.info("Pas d'historique pour l'analyse mensuelle")
                return
            
            # Statistiques
            total_tracks = len(monthly_history)
            unique_days = len(set(
                datetime.fromtimestamp(e.timestamp).date() 
                for e in monthly_history
            ))
            avg_per_day = total_tracks / unique_days if unique_days > 0 else 0
            
            # Artistes top
            artists = Counter()
            for entry in monthly_history:
                db_track = db.query(Track).get(entry.track_id)
                if db_track and db_track.album and db_track.album.artists:
                    for artist in db_track.album.artists:
                        artists[artist.name] += 1
            
            top_artists = artists.most_common(10)
            
            logger.info(f"📊 Analyse mensuelle:")
            logger.info(f"  - Total écoutes: {total_tracks}")
            logger.info(f"  - Jours actifs: {unique_days}")
            logger.info(f"  - Moyenne/jour: {avg_per_day:.1f}")
            logger.info(f"  - Top artiste: {top_artists[0] if top_artists else 'N/A'}")
            self._record_execution('monthly_analysis', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse mensuelle: {e}")
            self._record_execution('monthly_analysis', 'error', str(e))
        finally:
            db.close()
    
    async def _optimize_ai_descriptions(self):
        """
        AI optimization task: Generate AI descriptions for top 10 most-played albums.
        
        Runs every 6 hours via CronTrigger (hour='*/6'). Finds top 10 most-listened albums
        (by ListeningHistory play count) lacking AI descriptions (Metadata.ai_info IS NULL).
        Generates AI-powered album info prompt and persists to Metadata table. Gracefully
        degrades on per-album failures (continues processing others).
        
        Performance:
        - Typical: 30-90s (10 albums × 3-9s each for AI generation)
        - Database: 1 complex join query (Album/Track/ListeningHistory/Metadata), 0-10 INSERT
        - AI generation: 3-9s per album (Euria API call, typical 3-4s with caching)
        - Big-O: O(n) where n = 10 albums (fixed limit)
        - Scale: Constant time, independent of total album count
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Queries Album, Track, ListeningHistory, Metadata tables (complex join)
        - Calls AIService.generate_album_info (external API, 3-9s per album)
        - Inserts new Metadata rows for albums missing descriptions
        - Commits to database after each album (0-10 commits)
        - Records task execution in ScheduledTaskExecution table
        
        Logging:
        - INFO: Startup log (🤖 Optimisation descriptions IA)
        - INFO: Per-album success with play count (✨ Description IA ajoutée: <title> (<count> écoutes))
        - ERROR: Per-album failure (caught, continues to next)
        - INFO: Summary with count generated (🤖 Optimisation terminée: 6 descriptions générées)
        - ERROR: On catastrophic failure (recorded to DB)
        - DEBUG: Via _record_execution()
        
        Implementation Notes:
        - Database join: Album JOIN Track ON LEFT JOIN ListeningHistory RIGHT OUTER JOIN Metadata
        - Filter: Metadata.ai_info == None (outerjoin ensures nulls included)
        - Group by: Album.id (aggregates all plays)
        - Order by: COUNT(ListeningHistory.id) DESC (most-played first)
        - Limit: 10 albums max (constant time, reasonable AI cost)
        - Artist extraction: First artist (album.artists[0].name)
        - Fallback: Skips album if not found or no artists (graceful degradation)
        - AI prompt: "generate_album_info(artist_name, album_title)"
        - Database: Metadata(album_id, ai_info) - 1:1 relationship
        - Error recovery: db.rollback() on per-album error (preserves prior commits)
        - Called by: APScheduler trigger every 6 hours
        - Idempotent: Safe to call multiple times (only enriches missing descriptions)
        
        Example:
            # Called automatically by scheduler every 6 hours
            # Finds user's 10 most-played albums without AI descriptions
            # If Radiohead "OK Computer" has 342 plays and missing description:
            # Logs: "🤖 Optimisation descriptions IA"
            # Logs: "✨ Description IA ajoutée: OK Computer (342 écoutes)"
            # Logs: "🤖 Optimisation terminée: 8 descriptions générées"
        """
        logger.info("🤖 Optimisation descriptions IA")
        db = SessionLocal()
        
        try:
            # Trouver albums les plus écoutés sans description IA
            from sqlalchemy import func
            
            popular_albums = db.query(
                Album.id,
                Album.title,
                func.count(ListeningHistory.id).label('play_count')
            ).join(Track).join(ListeningHistory).outerjoin(Metadata).filter(
                Metadata.ai_info == None
            ).group_by(Album.id).order_by(
                func.count(ListeningHistory.id).desc()
            ).limit(10).all()
            
            generated = 0
            for album_id, album_title, play_count in popular_albums:
                try:
                    album = db.query(Album).get(album_id)
                    if not album or not album.artists:
                        continue
                    
                    artist_name = album.artists[0].name
                    
                    # Générer description
                    ai_info = await self.ai.generate_album_info(artist_name, album_title)
                    if ai_info:
                        metadata = Metadata(
                            album_id=album_id,
                            ai_info=ai_info
                        )
                        db.add(metadata)
                        db.commit()
                        generated += 1
                        logger.info(f"✨ Description IA ajoutée: {album_title} ({play_count} écoutes)")
                
                except Exception as e:
                    logger.error(f"Erreur description {album_title}: {e}")
                    db.rollback()
                    continue
            
            logger.info(f"🤖 Optimisation terminée: {generated} descriptions générées")
            self._record_execution('optimize_ai_descriptions', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur optimisation IA: {e}")
            self._record_execution('optimize_ai_descriptions', 'error', str(e))
        finally:
            db.close()
    
    async def _generate_random_haikus(self):
        """
        Generate markdown presentation of 5 random albums with AI-generated haikus.
        
        Runs at 06:00 UTC daily via CronTrigger. Selects 5 random Discogs albums, generates
        global haiku poem (fallback to default), creates per-album sections with AI-generated
        descriptions (35 words max, French), adds cover images and metadata links (Spotify/Discogs).
        Saves markdown file to data/scheduled-output with timestamp, format identical to API
        /collection/markdown/presentation endpoint for consistency. Calls _cleanup_old_files()
        to maintain max 5 haiku export files on disk (configurable via scheduler config).
        
        Performance:
        - Typical: 15-45s (5 albums × 3-9s AI calls per album + file I/O)
        - Database: 2 queries (Album count, random sample)
        - AI generation: 1 global + 5 per-album = 6x ~3-4s AI calls
        - File I/O: 200kb markdown write + 1 directory scan for cleanup
        - Big-O: O(n) where n=5 (fixed album count)
        - Disk: Creates ~200kb file, cleanup deletes old files to stay under limit
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Queries Album, Image tables (read-only)
        - Calls AIService.ask_for_ia() 6 times (1 global + 5 per-album)
        - Writes markdown file to data/scheduled-output/generate-haiku-TIMESTAMP.md
        - Calls _cleanup_old_files() to maintain file count limits
        - Records task execution in ScheduledTaskExecution table
        
        Logging:
        - INFO: Startup log (🎋 Génération haikus pour 5 albums random)
        - WARNING: If <5 albums in collection (graceful degradation)
        - WARNING: Per-album AI description failure (fallback used)
        - INFO: Success with file path (✅ Haikus sauvegardés: {filepath})
        - INFO: Format confirmation (📄 Format: Album Haïku)
        - ERROR: On catastrophic exception (full traceback logged)
        - DEBUG: Via _record_execution()
        
        File Format:
        - Header: # Album Haïku
        - Date: #### The D of MONTH, YYYY (platform-specific day formatting)
        - Album count: Indented count line
        - Global haiku: 3 lines (default: "Musique qui danse...")
        - Separator: ---
        - Per album (5x):
          - Title: # Artist Name
          - Info: #### Album Title (Year)
          - Links: Spotify and Discogs URLs
          - Support: 💿 Vinyl/CD/Digital
          - Description: AI-generated or fallback (35 word limit)
          - Image: <img src='url' /> HTML tag
          - Separator: ---
        - Footer: Python generated with love attribution line
        
        Implementation Notes:
        - Random selection: random.sample(all_albums, 5) for uniform distribution
        - Album filtering: Album.source == 'discogs' (only user-owned albums)
        - Date formatting: Platform-specific strftime (%-d on Unix, %#d on Windows)
        - Global haiku prompt: French language, 3-line format, no numbering
        - Per-album description: 35 word limit, French only
        - Fallback haiku: Hardcoded 3-line default if AI fails
        - Fallback description: Auto-generated from title/year if AI fails
        - Image source: album.images[0].url (first image only)
        - Output directory: Determined by config['scheduler']['output_dir'] or 'Scheduled Output'
        - File naming: "generate-haiku-YYYYMMDD-HHMMSS.md"
        - Cleanup: Calls _cleanup_old_files() to maintain max 5 haiku files
        - Task ID: 'generate_haiku_scheduled' (different from _weekly_haiku)
        - Called by: APScheduler trigger at 06:00 UTC daily
        - Idempotent: Safe to call multiple times (always generates new file with timestamp)
        
        Example:
            # Called automatically by scheduler at 06:00 UTC
            # Selects 5 random albums from user's Discogs collection
            # Generates markdown with AI haikus and descriptions
            # Logs: "🎋 Génération haikus pour 5 albums random - Format API"
            # Logs: "✅ Haikus sauvegardés: /path/to/generate-haiku-20260207-060000.md"
            # Logs: "📄 Format: Album Haïku (identique à API)"
        """
        import random
        
        logger.info("🎋 Génération haikus pour 5 albums random - Format API")
        db = SessionLocal()
        
        try:
            # Récupérer 5 albums aléatoires
            all_albums = db.query(Album).filter(Album.source == 'discogs').all()
            if len(all_albums) < 5:
                logger.warning("Pas assez d'albums pour générer haikus")
                return
            
            selected_albums = random.sample(all_albums, 5)
            
            # Générer markdown - Format IDENTIQUE à l'API
            markdown = "# Album Haïku\n"
            
            # Date du jour
            now = datetime.now()
            # Formater la date: "The 1 of February, 2026"
            day = now.strftime("%-d" if os.name != 'nt' else "%#d")  # Pas de zéro au jour
            month = now.strftime("%B")
            year = now.strftime("%Y")
            date_str = f"#### The {day} of {month}, {year}"
            markdown += f"{date_str}\n"
            markdown += f"\t\t{len(selected_albums)} albums from Discogs collection\n"
            
            # Haïku global
            haiku_text = ""
            try:
                haiku_prompt = "Génère un haïku court sur la musique et les albums. Réponds uniquement avec le haïku en 3 lignes, sans numérotation."
                haiku_text = await self.ai.ask_for_ia(haiku_prompt, max_tokens=100)
                # Ajouter chaque ligne du haïku avec indentation
                for line in haiku_text.strip().split('\n'):
                    markdown += f"\t\t{line.strip()}\n"
            except Exception as e:
                logger.warning(f"⚠️ Erreur génération haïku global: {e}")
                # Haïku par défaut
                markdown += "\t\tMusique qui danse,\n"
                markdown += "\t\talbums en harmonie,\n"
                markdown += "\t\tcœur qui s'envole.\n"
            
            markdown += "---\n"
            
            # Générer une section pour chaque album
            for album in selected_albums:
                # Artiste en titre
                if album.artists:
                    artist_name = album.artists[0].name
                    markdown += f"# {artist_name}\n"
                
                # Titre, année et infos
                title_line = f"#### {album.title}"
                if album.year:
                    title_line += f" ({album.year})"
                markdown += f"{title_line}\n"
                
                # Liens Spotify et Discogs
                markdown += "\t###### 🎧"
                if album.spotify_url:
                    markdown += f" [Listen with Spotify]({album.spotify_url})"
                markdown += "  👥"
                if album.discogs_url:
                    markdown += f" [Read on Discogs]({album.discogs_url})"
                markdown += "\n\t###### 💿 "
                markdown += f"{album.support if album.support else 'Digital'}\n"
                
                # Description générée par l'IA
                description = ""
                try:
                    album_lower = album.title.lower()
                    artist_lower = (album.artists[0].name.lower() if album.artists else "artiste inconnu")
                    description_prompt = f"""Présente moi l'album {album_lower} de {artist_lower}. 
N'ajoute pas de questions ou de commentaires. 
Limite ta réponse à 35 mots maximum.
Réponds uniquement en français."""
                    description = await self.ai.ask_for_ia(description_prompt, max_tokens=100)
                    
                    # Fallback si pas de description
                    if not description or len(description) < 10:
                        description = f"Album {album.title} sorti en {album.year if album.year else '?'}. Œuvre musicale enrichissante, à découvrir absolument."
                except Exception as e:
                    logger.warning(f"⚠️ Erreur génération description pour {album.title}: {e}")
                    description = f"Album {album.title} sorti en {album.year if album.year else '?'}. Œuvre musicale enrichissante, à découvrir absolument."
                
                # Ajouter la description avec indentation
                description = description.strip()
                for line in description.split('\n'):
                    markdown += f"\t\t{line}\n"
                
                # Image HTML
                if album.images and album.images[0].url:
                    image_url = album.images[0].url
                    markdown += f"\n\n<img src='{image_url}' />\n"
                
                markdown += "---\n"
            
            # Footer
            markdown += "\t\tPython generated with love, for iA Presenter using Euria AI from Infomaniak\n"
            
            # Créer chemin absolu pour le répertoire de sortie
            current_dir = os.path.abspath(__file__)
            for _ in range(4):
                current_dir = os.path.dirname(current_dir)
            project_root = current_dir
            output_dir = os.path.join(project_root, self.config.get('scheduler', {}).get('output_dir', 'Scheduled Output'))
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Générer nom fichier avec date/heure
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"generate-haiku-{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            
            # Sauvegarder fichier
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            logger.info(f"✅ Haikus sauvegardés: {filepath}")
            logger.info(f"📄 Format: Album Haïku (identique à API)")
            
            # Nettoyer les anciens fichiers
            self._cleanup_old_files()
            self._record_execution('generate_haiku_scheduled', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur génération haikus: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._record_execution('generate_haiku_scheduled', 'error', str(e))
        finally:
            db.close()
    
    async def _export_collection_markdown(self):
        """
        Export complete music collection as markdown with table of contents.
        
        Runs at 08:00 UTC daily via CronTrigger. Uses MarkdownExportService.get_collection_markdown()
        (same as API endpoint) to export entire collection with TOC, sorted by artist/year/title,
        includes album metadata (year, support, Discogs ID, AI info). Saves to timestamped
        markdown file in data/scheduled-output directory. Calls _cleanup_old_files() to maintain
        max 5 markdown export files on disk.
        
        Performance:
        - Typical: 500ms - 5s (depends on collection size: 100-1000 albums)
        - Database: 1-2 Album queries (Album.source == 'discogs'), full load into memory
        - Markdown generation: In-memory O(n) string concatenation
        - File I/O: 100kb - 500kb file write (typical: 200-300kb)
        - Big-O: O(n) where n = total albums in user's collection
        - Scale: Handles 10,000+ album collections (typical: 100-500 albums)
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Queries Album, Artist, Metadata, Image tables (read-only, full load)
        - Writes markdown file to data/scheduled-output/export-markdown-TIMESTAMP.md
        - Calls _cleanup_old_files() to maintain file count limits
        - Records task execution in ScheduledTaskExecution table
        
        Logging:
        - INFO: Startup log (📝 Export collection en markdown)
        - WARNING: If no albums found
        - INFO: Success with file path (✅ Collection markdown sauvegardée: {filepath})
        - ERROR: On exception during export
        - DEBUG: Via _record_execution()
        
        File Format:
        - Generated by MarkdownExportService.get_collection_markdown()
        - Section 1: Header with export timestamp and album count
        - Section 2: Table of contents with header anchor links
        - Sections 3+: By-artist sections with:
          - Artist name (heading 1)
          - Per-album entries with:
            - Album title and year (heading 4)
            - Support type (Vinyl/CD/Digital)
            - Discogs ID (if present)
            - Spotify URL (if present)
            - AI description (if present)
            - Cover image (if present)
        
        Implementation Notes:
        - Service reuse: MarkdownExportService (API consistency)
        - Markdown content: Generated once via service method
        - Empty collection handling: Returns empty string, logs warning
        - Output directory: Determined by config['scheduler']['output_dir'] or 'Scheduled Output'
        - File naming: "export-markdown-YYYYMMDD-HHMMSS.md"
        - File encoding: UTF-8 (supports accented characters in French album names)
        - Cleanup: Calls _cleanup_old_files() to maintain max 5 files
        - Task ID: 'export_collection_markdown'
        - Called by: APScheduler trigger at 08:00 UTC daily
        - Idempotent: Safe to call multiple times (always generates new file with timestamp)
        - API parity: Format identical to GET /collection/markdown API response
        
        Example:
            # Called automatically by scheduler at 08:00 UTC
            # Exports all 342 Discogs albums to markdown
            # Logs: "📝 Export collection en markdown"
            # Logs: "✅ Collection markdown sauvegardée: /path/to/export-markdown-20260207-080000.md"
        """
        logger.info("📝 Export collection en markdown")
        db = SessionLocal()
        
        try:
            # Utiliser le même service que l'API pour garantir l'identité du format
            markdown_content = MarkdownExportService.get_collection_markdown(db)
            
            if not markdown_content:
                logger.warning("Aucun album à exporter")
                return
            
            # Créer chemin absolu pour le répertoire de sortie
            current_dir = os.path.abspath(__file__)
            for _ in range(4):
                current_dir = os.path.dirname(current_dir)
            project_root = current_dir
            output_dir = os.path.join(project_root, self.config.get('scheduler', {}).get('output_dir', 'Scheduled Output'))
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Générer nom fichier avec date/heure
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"export-markdown-{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            
            # Sauvegarder fichier
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"✅ Collection markdown sauvegardée: {filepath}")
            
            # Nettoyer les anciens fichiers
            self._cleanup_old_files()
            self._record_execution('export_collection_markdown', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur export markdown: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._record_execution('export_collection_markdown', 'error', str(e))
        finally:
            db.close()
    
    async def _export_collection_json(self):
        """
        Export complete music collection as structured JSON with full metadata.
        
        Runs at 10:00 UTC daily via CronTrigger. Queries all Discogs albums, constructs JSON
        with export metadata (timestamp, album count) and per-album data (title, artists, year,
        support type, IDs, URLs, images, metadata). Saves to timestamped JSON file in
        data/scheduled-output directory. Calls _cleanup_old_files() to maintain max 5 JSON
        files on disk (configurable via scheduler config).
        
        Performance:
        - Typical: 1-5s (depends on collection size + metadata load)
        - Database: 1 Album query (sorted by title), iterative Image/Metadata loads
        - JSON serialization: In-memory O(n) with datetime formatting
        - File I/O: 100kb - 500kb file write (typical: 200-300kb)
        - Big-O: O(n*m) where n = albums, m = avg images per album
        - Scale: Handles 10,000+ album collections (typical: 100-500 albums)
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Queries Album, Artist, Image, Metadata tables (read-only, full load)
        - Writes JSON file to data/scheduled-output/export-json-TIMESTAMP.json
        - Calls _cleanup_old_files() to maintain file count limits
        - Records task execution in ScheduledTaskExecution table
        
        Logging:
        - INFO: Startup log (📊 Export collection en JSON)
        - WARNING: If no albums found
        - INFO: Success with file path (✅ Collection JSON sauvegardée: {filepath})
        - ERROR: On exception during export
        - DEBUG: Via _record_execution()
        
        JSON Structure:
        ```json
        {
          "export_date": "2026-02-07T10:00:00.123456",
          "total_albums": 342,
          "albums": [
            {
              "id": "550e8400-e29b-41d4-a716-446655440000",
              "title": "OK Computer",
              "artists": ["Radiohead"],
              "year": 1997,
              "support": "Vinyl",
              "discogs_id": "123456",
              "spotify_url": "https://open.spotify.com/album/...",
              "discogs_url": "https://www.discogs.com/release/...",
              "images": [
                {
                  "url": "https://example.com/image.jpg",
                  "type": "album",
                  "source": "discogs"
                }
              ],
              "created_at": "2025-01-15T12:30:45.123456",
              "metadata": {
                "ai_info": "Epic 90s album with electronic influences...",
                "resume": "Thom Yorke vocal masterpiece",
                "labels": ["Parlophone"],
                "film_title": null,
                "film_year": null,
                "film_director": null
              }
            },
            ...
          ]
        }
        ```
        
        Implementation Notes:
        - Album filtering: Album.source == 'discogs' (only user-owned)
        - Sorting: By album title (alphabetical)
        - Image iteration: album.images list (can be empty)
        - Image structure: {url, image_type, source} from Image model
        - Metadata structure: {ai_info, resume, labels, film_title, film_year, film_director}
        - Null handling: created_at nullable, metadata fields can be null
        - Artists: List comprehension of artist.name values
        - ISO8601 dates: datetime.isoformat() for all timestamps
        - Output directory: Determined by config['scheduler']['output_dir'] or 'Scheduled Output'
        - File naming: "export-json-YYYYMMDD-HHMMSS.json"
        - File encoding: UTF-8 with UTF-8 sig (Python json.dumps() default)
        - Cleanup: Calls _cleanup_old_files() to maintain max 5 files
        - Task ID: 'export_collection_json'
        - Called by: APScheduler trigger at 10:00 UTC daily
        - Idempotent: Safe to call multiple times (always generates new file with timestamp)
        - Use cases: Data backup, third-party integrations, spreadsheet import
        
        Example:
            # Called automatically by scheduler at 10:00 UTC
            # Exports all 342 Discogs albums to JSON with full metadata
            # Logs: "📊 Export collection en JSON"
            # Logs: "✅ Collection JSON sauvegardée: /path/to/export-json-20260207-100000.json"
        """
        logger.info("📊 Export collection en JSON")
        db = SessionLocal()
        
        try:
            # Récupérer tous les albums de collection Discogs avec eager loading, triés par titre
            albums = db.query(Album).filter(Album.source == 'discogs').options(
                joinedload(Album.artists),
                joinedload(Album.images),
                joinedload(Album.album_metadata)
            ).order_by(Album.title).all()
            
            if not albums:
                logger.warning("Aucun album à exporter")
                return
            
            # Construire les données JSON avec le même format que l'API
            data = {
                "export_date": datetime.now().isoformat(),
                "total_albums": len(albums),
                "albums": []
            }
            
            for album in albums:
                # Traiter les images
                images = []
                if album.images:
                    for img in album.images:
                        images.append({
                            "url": img.url,
                            "type": img.image_type,
                            "source": img.source
                        })
                
                # Traiter les métadonnées
                metadata = {}
                if album.album_metadata:
                    meta = album.album_metadata
                    metadata = {
                        "ai_info": meta.ai_info,
                        "resume": meta.resume,
                        "labels": meta.labels,
                        "film_title": meta.film_title,
                        "film_year": meta.film_year,
                        "film_director": meta.film_director
                    }
                
                album_data = {
                    "id": album.id,
                    "title": album.title,
                    "artists": [artist.name for artist in album.artists],
                    "year": album.year,
                    "support": album.support,
                    "discogs_id": album.discogs_id,
                    "spotify_url": album.spotify_url,
                    "discogs_url": album.discogs_url,
                    "images": images,
                    "created_at": album.created_at.isoformat() if album.created_at else None,
                    "ai_description": album.ai_description,
                    "metadata": metadata
                }
                
                data["albums"].append(album_data)
            
            # Créer chemin absolu pour le répertoire de sortie
            current_dir = os.path.abspath(__file__)
            for _ in range(4):
                current_dir = os.path.dirname(current_dir)
            project_root = current_dir
            output_dir = os.path.join(project_root, self.config.get('scheduler', {}).get('output_dir', 'Scheduled Output'))
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Générer nom fichier avec date/heure
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"export-json-{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Sauvegarder fichier
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Collection JSON sauvegardée: {filepath}")
            
            # Nettoyer les anciens fichiers
            self._cleanup_old_files()
            self._record_execution('export_collection_json', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur export JSON: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._record_execution('export_collection_json', 'error', str(e))
        finally:
            db.close()
    
    def _cleanup_old_files(self):
        """
        Clean up old export files and maintain max file count per type.
        
        Called by export task methods (_generate_random_haikus, _export_collection_markdown,
        _export_collection_json) to maintain disk usage limits. Queries file system for all
        export files matching type patterns (generate-haiku-*.md, export-markdown-*.md,
        export-json-*.json), sorts by modification time, deletes oldest files to stay below
        max_files_per_type limit (default: 5 files per type).
        
        Performance:
        - Typical: 50-200ms (filesystem glob + sorting + unlink operations)
        - Filesystem: glob() for pattern matching (3 patterns), stat() for mtime
        - Cleanup: O(n) where n = total files exceeding limit
        - Scale: ~100-500 files max (5 types × 25 files each worst case)
        - Latency: Negligible, async-safe (called by async tasks synchronously)
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Lists files in data/scheduled-output directory (filesystem read)
        - Deletes old files from disk (filesystem write, permanent)
        - Logs file deletion (🗑️ Supprimé fichier ancien)
        
        Logging:
        - INFO: Per-deleted file (🗑️ Supprimé fichier ancien ({file_type}): {filename})
        - ERROR: On unlink failure (❌ Erreur suppression {filepath}: {e})
        - No logging if files under limit (silent success)
        
        Configuration:
        - Read from config['scheduler']['max_files_per_type'] (default: 5)
        - Read from config['scheduler']['output_dir'] (default: 'Scheduled Output')
        - Directory searched: {project_root}/{output_dir}/
        
        File Patterns:
        - Haiku exports: "generate-haiku-*.md" → file_type='haiku'
        - Markdown exports: "export-markdown-*.md" → file_type='markdown'
        - JSON exports: "export-json-*.json" → file_type='json'
        
        Implementation Notes:
        - Output directory calculation: Same 4-level parent traversal as exports
        - glob.glob() returns unsorted, must sort by mtime
        - Sorting: os.path.getmtime() for modification timestamp
        - Deletion: Keep newest max_files, delete all older ones if count > limit
        - Safe deletion: Catches individual file errors, continues to next file
        - Idempotent: Safe to call multiple times (no-op if files under limit)
        - No recursion: Only searches output directory root (not subdirs)
        - Non-blocking: Synchronous I/O OK, typically <200ms (negligible delay)
        - Use cases: Called after every export task to prevent disk bloat
        
        Example:
            # Called automatically by _generate_random_haikus, etc.
            # If output_dir has 8 haiku files and max=5:
            # Logs: "🗑️ Supprimé fichier ancien (haiku): generate-haiku-20260205-060000.md"
            # Logs: "🗑️ Supprimé fichier ancien (haiku): generate-haiku-20260204-060000.md"
            # Logs: "🗑️ Supprimé fichier ancien (haiku): generate-haiku-20260203-060000.md"
            # (keeps 5 newest files, deletes 3 oldest)
        """
        import glob
        
        max_files = self.config.get('scheduler', {}).get('max_files_per_type', 5)
        
        # Calculer le chemin du répertoire de sortie
        current_dir = os.path.abspath(__file__)
        for _ in range(4):
            current_dir = os.path.dirname(current_dir)
        project_root = current_dir
        output_dir = os.path.join(project_root, self.config.get('scheduler', {}).get('output_dir', 'Scheduled Output'))
        
        if not os.path.exists(output_dir):
            return
        
        # Définir les patterns pour chaque type de fichier
        file_patterns = {
            'generate-haiku-*.md': 'haiku',
            'export-markdown-*.md': 'markdown',
            'export-json-*.json': 'json'
        }
        
        for pattern, file_type in file_patterns.items():
            files = glob.glob(os.path.join(output_dir, pattern))
            
            if len(files) > max_files:
                # Trier par date de modification (les plus anciens en premier)
                files_sorted = sorted(files, key=lambda x: os.path.getmtime(x))
                
                # Supprimer les fichiers en excès (garder seulement les max_files les plus récents)
                files_to_delete = files_sorted[:-max_files]
                
                for file_path in files_to_delete:
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️ Supprimé fichier ancien ({file_type}): {os.path.basename(file_path)}")
                    except Exception as e:
                        logger.error(f"❌ Erreur suppression {file_path}: {e}")
    
    async def enrich_imported_albums(self, albums_to_enrich: dict) -> dict:
        """
        Enrich newly imported albums with Spotify URLs, images, and AI descriptions.
        
        Public task method called by import endpoints to asynchronously enrich albums in background.
        Iterates through albums_to_enrich dict (keyed by album UUID), searches Spotify for
        URL + image, queries LastFM for image fallback, generates AI-powered album metadata
        (resume, labels, etc.). Commits database changes in batches (every 10 albums) and
        flushes frequently (every 50 albums) to avoid connection locks. Returns enrichment
        summary (count, total, status) regardless of partial failures.
        
        Args:
            albums_to_enrich (dict): Album dict with structure:
                {
                  'uuid_key': {
                    'album_id': 'abc123...',
                    'artist': 'Radiohead',
                    'title': 'OK Computer'
                  },
                  ...
                }
        
        Returns:
            dict: Enrichment summary with keys:
                - status (str): 'completed' if success, 'error' if catastrophic
                - albums_enriched (int): Count of successfully enriched albums
                - total_albums (int): Total albums requested for enrichment
                - error (str, optional): Error message if status='error'
        
        Performance:
        - Typical: 5-30s (depends on album count and Spotify API availability)
        - Database: ~3 commits per album (every 10), frequent flushes
        - Spotify API: 1-2 calls per album (~100-200ms each), timeout 5s
        - LastFM API: 0-1 call per album if Spotify image failed (~100-300ms)
        - AI generation: 1 call per album (~3-9s), timeout 45s
        - Big-O: O(n*m) where n = album count, m = avg API calls per album (3-4)
        - Scale: Typical: 5-50 albums (50 albums = 30-60s, reasonable background task)
        
        Raises:
        - No exceptions raised to caller (returns error dict instead)
        - Databases errors caught, task continues (partial success)
        
        Side Effects:
        - Updates Album.spotify_url if found via Spotify search
        - Creates new Image records for Spotify/LastFM album art
        - Creates/updates Metadata records with AI-generated info
        - Commits to database every 10 albums (with log)
        - Flushes connection every 50 albums (prevents lock timeouts)
        - Calls external APIs: Spotify, LastFM, Euria AI
        - Updates self.last_executions['enrich_imported_albums'] timestamp
        
        Logging:
        - INFO: Startup with album count
        - INFO: Per-album progress (🎨 Enrichissement album N/TOTAL: Artist - Title)
        - INFO: Per-10-album checkpoint (💾 N/TOTAL albums enrichis...)
        - WARNING: Per-album Spotify failure (non-blocking, continues)
        - WARNING: Per-album LastFM failure (non-blocking, continues)
        - WARNING: Per-album AI failure (non-blocking, uses fallback)
        - ERROR: Catastrophic failure (recorded to DB)
        
        Implementation Notes:
        - Input structure: albums_to_enrich.values() is iterable of album dicts
        - Enumeration: Starts at 1 for user-friendly logging (1-indexed counts)
        - Album lookup: db.query(Album).filter_by(id=album_id).first()
        - Spotify search: self.spotify.search_album_url(artist, title)
        - Spotify image: self.spotify.search_album_image(artist, title)
        - LastFM integration: Dynamically imported, instantiated per album if needed
        - AI generation: self.ai.generate_album_info(artist, title)
        - Image model: Image(url, image_type='album', source='spotify'|'lastfm', album_id)
        - Metadata model: Metadata(album_id, ai_info) with optional resume/labels
        - Database batching: Explicit commit() every 10, flush() every 50
        - Error handling: Catch-continue on per-album errors, rollback per album
        - Task tracking: last_executions dict updated at start (timestamp recorded)
        - Idempotent: Can be called multiple times (incremental enrichment)
        - Called by: Import API endpoints (POST /collection/import)
        
        Example Input:
            {
              '1': {'album_id': 'xxx', 'artist': 'Radiohead', 'title': 'OK Computer'},
              '2': {'album_id': 'yyy', 'artist': 'Björk', 'title': 'Debut'},
              ...
            }
        
        Example Output (Success):
            {
              'status': 'completed',
              'albums_enriched': 8,
              'total_albums': 10
            }
        
        Example Output (Partial Failure):
            {
              'status': 'completed',
              'albums_enriched': 7,
              'total_albums': 10
              # 3 albums enriched partially or skipped
            }
        
        Example Output (Catastrophic):
            {
              'status': 'error',
              'error': 'Database connection lost',
              'albums_enriched': 2,
              'total_albums': 10
            }
        """
        self.last_executions['enrich_imported_albums'] = datetime.now(timezone.utc).isoformat()
        logger.info(f"🎨 Enrichissement de {len(albums_to_enrich)} albums importés (en arrière-plan)")
        db = SessionLocal()
        
        enriched_count = 0
        total_albums = len(albums_to_enrich)
        
        try:
            for album_index, album_info in enumerate(albums_to_enrich.values(), 1):
                try:
                    album_id = album_info['album_id']
                    artist = album_info['artist']
                    title = album_info['title']
                    
                    logger.info(f"🎨 Enrichissement album {album_index}/{total_albums}: {artist} - {title}")
                    
                    album = db.query(Album).filter_by(id=album_id).first()
                    if not album:
                        continue
                    
                    # Enrichir Spotify
                    if not album.spotify_url:
                        try:
                            spotify_url = await self.spotify.search_album_url(artist, title)
                            if spotify_url:
                                album.spotify_url = spotify_url
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur Spotify pour {title}: {e}")
                    
                    # Images Spotify
                    if not any(img.source == 'spotify' for img in album.images):
                        try:
                            from app.models import Image
                            album_image = await self.spotify.search_album_image(artist, title)
                            if album_image:
                                img = Image(
                                    url=album_image,
                                    image_type='album',
                                    source='spotify',
                                    album_id=album.id
                                )
                                db.add(img)
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur image Spotify pour {title}: {e}")
                    
                    # Images Last.fm (appel direct HTTP)
                    if not any(img.source == 'lastfm' for img in album.images):
                        try:
                            from app.services.lastfm_service import LastFMService
                            from config.settings import get_settings
                            settings = get_settings()
                            secrets = settings.secrets
                            lastfm_config = secrets.get('lastfm', {})
                            lastfm_service = LastFMService(
                                api_key=lastfm_config.get('api_key'),
                                api_secret=lastfm_config.get('api_secret'),
                                username=lastfm_config.get('username')
                            )
                            lastfm_image = await lastfm_service.get_album_image(artist, title)
                            if lastfm_image:
                                from app.models import Image
                                img = Image(
                                    url=lastfm_image,
                                    image_type='album',
                                    source='lastfm',
                                    album_id=album.id
                                )
                                db.add(img)
                                logger.info(f"✅ Image Last.fm ajoutée pour {artist} - {title}")
                        except Exception as e:
                            logger.error(f"❌ Erreur image Last.fm pour {artist} - {title}: {e}")
                    
                    # Description IA
                    if not album.album_metadata or not album.album_metadata.ai_info:
                        try:
                            # Délai pour ne pas saturer l'API IA
                            import asyncio
                            await asyncio.sleep(1.0)
                            ai_info = await self.ai.generate_album_info(artist, title)
                            if ai_info:
                                if not album.album_metadata:
                                    metadata = Metadata(album_id=album.id, ai_info=ai_info)
                                    db.add(metadata)
                                else:
                                    album.album_metadata.ai_info = ai_info
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur IA pour {title}: {e}")
                    
                    enriched_count += 1
                    if enriched_count % 10 == 0:
                        db.commit()
                        logger.info(f"💾 {enriched_count}/{total_albums} albums enrichis...")
                    if enriched_count % 50 == 0:
                        db.flush()  # Flush plus souvent pour éviter les locks
                        
                except Exception as e:
                    logger.error(f"❌ Erreur enrichissement album: {e}")
                    db.rollback()
                    continue
            
            db.commit()
            logger.info(f"✅ Enrichissement d'import terminé: {enriched_count} albums enrichis")
            
            return {
                'status': 'completed',
                'albums_enriched': enriched_count,
                'total_albums': total_albums
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement import: {e}")
            db.rollback()
            return {
                'status': 'error',
                'error': str(e),
                'albums_enriched': enriched_count,
                'total_albums': total_albums
            }
        finally:
            db.close()
    
    async def _sync_discogs_daily(self):
        """
        Daily Discogs collection synchronization task: Import new/updated albums from user's Discogs.
        
        Runs at 04:00 UTC daily via CronTrigger. Imports service function _sync_discogs_task
        dynamically from tracking API module, executes with limit=None (all albums). Handles
        complete Discogs collection sync: queries user's Discogs profile, compares with local
        albums table, imports new releases, updates existing metadata (year, support, images).
        Gracefully degrades on Discogs API failures (continues with partial results).
        
        Performance:
        - Typical: 5-60s (depends on Discogs user collection size and pagination)
        - Database: 1 initial query (Collection count), 10-100 INSERT/UPDATE operations
        - Discogs API: Multiple paginated requests (200+ albums = 10+ API calls)
        - Discogs timeout: Per-page 10s timeout, 5 retry attempts
        - Big-O: O(n) where n = total albums in Discogs collection
        - Scale: Typical: 100-500 albums (5-30s), large: 1000+ albums (30-60s)
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Queries Discogs API (external, rate-limited, can timeout)
        - Creates new Album records for new Discogs releases
        - Updates existing Album metadata (year, support, images)
        - Commits to database (0-100+ inserts/updates per run)
        - Records task execution in ScheduledTaskExecution table
        - No local deletions (albums never removed, only added/updated)
        
        Logging:
        - INFO: Startup log (💿 Début synchronisation quotidienne Discogs)
        - INFO: Success log (✅ Synchronisation Discogs quotidienne terminée)
        - ERROR: On exception (logs by imported _sync_discogs_task)
        - DEBUG: Via _record_execution()
        
        Implementation Notes:
        - Dynamic import: from app.api.v1.tracking.services import _sync_discogs_task
        - Task invocation: await _sync_discogs_task(limit=None)
        - limit=None: Syncs entire collection (not limited to X albums)
        - Discogs authentication: User credentials loaded from config (secrets.json)
        - Rate limiting: Discogs API enforced server-side (60 req/min for unauthenticated)
        - Pagination: Automatic pagination by _sync_discogs_task (returns list of results)
        - Error recovery: Partial results allowed (continues if page fails)
        - Database: Transactional (all-or-nothing per page, partial commits allowed)
        - Idempotent: Safe to call multiple times (incremental sync, duplicates ignored)
        - Called by: APScheduler trigger at 04:00 UTC daily
        - Alternative trigger: Manual via trigger_task('sync_discogs_daily') API
        - Task ID: 'sync_discogs_daily' (used by _record_execution for tracking)
        
        Discogs Sync Process (by _sync_discogs_task):
        1. Load user's Discogs profile (username from config)
        2. Query Discogs collection endpoint (paginated)
        3. For each release in response:
           - Check if Album exists in local DB (by discogs_id)
           - If new: Create Album + Image + Artist relationships
           - If exists: Update year, support, images (merge strategy)
        4. Complete pagination loop (handle rate limiting delays)
        5. Return result summary
        
        Example:
            # Called automatically by scheduler at 04:00 UTC
            # User has 342 albums in Discogs, 320 already synced
            # Logs: "💿 Début synchronisation quotidienne Discogs"
            # (Processes Discogs API paginated response, adds 22 new albums)
            # Logs: "✅ Synchronisation Discogs quotidienne terminée"
        """
        logger.info("💿 Début synchronisation quotidienne Discogs")
        
        try:
            # Importer la fonction de sync depuis le API
            from app.api.v1.tracking.services import _sync_discogs_task
            
            # Exécuter la sync
            await _sync_discogs_task(limit=None)
            
            logger.info("✅ Synchronisation Discogs quotidienne terminée")
            self._record_execution('sync_discogs_daily', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sync Discogs quotidienne: {e}")
            self._record_execution('sync_discogs_daily', 'error', str(e))
    
    async def trigger_task(self, task_name: str) -> dict:
        """
        Manually trigger any scheduled background task with immediate execution.
        
        Public API method for on-demand task execution. Maps task_name string to task method,
        validates existence (prevents typos), executes method immediately (non-blocking via
        await). Returns execution result with status and timestamp. Used by admin endpoints
        to manually run exports, enrichment, haiku generation without waiting for scheduler.
        
        Args:
            task_name (str): Task identifier (must match scheduler job ID):
                - 'daily_enrichment': 02:00 UTC daily enrichment
                - 'generate_haiku_scheduled': 06:00 UTC random haiku generation
                - 'export_collection_markdown': 08:00 UTC markdown export
                - 'export_collection_json': 10:00 UTC JSON export
                - 'weekly_haiku': 20:00 Sunday haiku report
                - 'monthly_analysis': 03:00 1st month analysis
                - 'optimize_ai_descriptions': Every 6h optimization
                - 'generate_magazine_editions': 03:00 UTC magazine batch
                - 'sync_discogs_daily': 04:00 UTC Discogs sync
        
        Returns:
            dict: Execution result with keys:
                - task (str): task_name echoed back
                - status (str): 'completed' on success
                - timestamp (str): ISO8601 UTC datetime when triggered
        
        Raises:
            ValueError: If task_name not in tasks dict (invalid task_name)
        
        Performance:
        - Typical: Depends on task (see individual task performance)
        - Overhead: <1ms for mapping + validation
        - Execution: Awaits full task completion (blocking from caller perspective)
        - Returns: Immediate after task completion
        
        Side Effects:
        - Immediately executes mapped task method asynchronously
        - All side effects of target task apply (database writes, API calls, files)
        - Records execution in ScheduledTaskExecution via _record_execution()
        - Logs startup via task's own logger.info() calls
        
        Logging:
        - INFO: Manual trigger (🚀 Déclenchement manuel: {task_name})
        - All logs from target task method (mixed with caller's logs)
        - No ERROR logging (task errors logged within task method)
        
        Implementation Notes:
        - Task mapping: Hard-coded dict maps task_name to async method reference
        - Method callable: All tasks are async def, called with await tasks[task_name]()
        - Error handling: ValueError raised if task_name not found (caller catches)
        - Null return: Task methods return None, status hardcoded as 'completed'
        - Timestamp: datetime.now().isoformat() in UTC (local time - note: not UTC aware)
        - Idempotent: Safe to call multiple times (each call reruns task)
        - Blocking: await blocks until task completes (can be long: 30-60s for exports)
        - Task ID reuse: Uses same task IDs as scheduler (for _record_execution consistency)
        - Called by: Admin API endpoints (e.g., POST /admin/trigger-task)
        - Security: Should be restricted to authenticated admin users (caller's responsibility)
        
        Task Mapping:
        - daily_enrichment → self._daily_enrichment() (Spotify/year enrichment, 10-20s)
        - generate_haiku_scheduled → self._generate_random_haikus() (30-60s, 5 albums + AI)
        - export_collection_markdown → self._export_collection_markdown() (file write, 2-10s)
        - export_collection_json → self._export_collection_json() (JSON serialize, 2-10s)
        - weekly_haiku → self._weekly_haiku() (5-10s, listening history analysis)
        - monthly_analysis → self._monthly_analysis() (1-3s, stats calculation)
        - optimize_ai_descriptions → self._optimize_ai_descriptions() (30-90s, 10 AI calls)
        - generate_magazine_editions → self._generate_magazine_editions() (batch generation, variable)
        - sync_discogs_daily → self._sync_discogs_daily() (Discogs import, variable)
        
        Example:
            # Admin wants to manually trigger markdown export
            trigger_task('export_collection_markdown')
            # Returns:
            # {
            #   'task': 'export_collection_markdown',
            #   'status': 'completed',
            #   'timestamp': '2026-02-07T10:15:30.123456'
            # }
            
            # Admin typos task name
            trigger_task('export_markdown')  # ValueError: Tâche inconnue: export_markdown
        """
        tasks = {
            'daily_enrichment': self._daily_enrichment,
            'generate_haiku_scheduled': self._generate_random_haikus,
            'export_collection_markdown': self._export_collection_markdown,
            'export_collection_json': self._export_collection_json,
            'weekly_haiku': self._weekly_haiku,
            'monthly_analysis': self._monthly_analysis,
            'optimize_ai_descriptions': self._optimize_ai_descriptions,
            'generate_magazine_editions': self._generate_magazine_editions,
            'sync_discogs_daily': self._sync_discogs_daily
        }
        
        if task_name not in tasks:
            raise ValueError(f"Tâche inconnue: {task_name}")
        
        logger.info(f"🚀 Déclenchement manuel: {task_name}")
        await tasks[task_name]()
        
        return {
            'task': task_name,
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        }
    
    async def _generate_magazine_editions(self):
        """
        Generate pre-made magazine editions for frontend caching and frontend surprise feature.
        
        Runs at 03:00 UTC daily via CronTrigger (same time as Discogs sync, 1 hour before exports).
        Intelligently generates 10 magazine editions with 30-minute staggered delays (avoids
        connection pool exhaustion). Performs automatic garbage collection: deletes editions
        older than 30 days, removes excess editions if count exceeds 100 max (keeps newest).
        Leverages MagazineEditionService for generation (complex AI layout + album selection).
        
        Performance:
        - Typical: 15-60 minutes (10 editions × 90-360s per edition = 900-3600s total)
        - Generation: Sequential with 30-minute delays between starts
        - Database: ~10 inserts (editions), 1-2 cleanup SUMs/DELETEs
        - File I/O: Writes 10 JSON edition files to data/magazine-editions/
        - AI calls: 50+ Euria calls (5 per edition × 10 editions, layout descriptions)
        - Big-O: O(n) where n = 10 editions (fixed batch size)
        - Concurrency: Sequential with delays (not parallelized, prevents resource exhaustion)
        
        Raises:
        - No exceptions raised (all caught and logged, task continues)
        
        Side Effects:
        - Queries Album, Artist, metadata tables via MagazineEditionService
        - Calls AIService 50+ times for AI-powered layout descriptions
        - Creates 10 JSON files in data/magazine-editions/{YYYY-MM-DD}/00{NN}/
        - Inserts 10 Edition rows in database (with generated_at timestamp)
        - Deletes Edition rows older than 30 days (data retention policy)
        - Deletes oldest Edition rows if count > 100 (disk quota enforcement)
        - Records task execution in ScheduledTaskExecution table
        - Logs detailed progress (success count, cleanup counts)
        
        Logging:
        - INFO: Startup log (📰 Début génération lot de magazines)
        - INFO: Summary with all counts (✅ Génération magazines terminée: 10 créées, 2 anciennes supprimées, 0 excédent supprimé)
        - ERROR: On exception (recorded to DB)
        - DEBUG: Via _record_execution()
        
        Implementation Notes:
        - MagazineEditionService: Instantiated fresh with SessionLocal() db session
        - Batch generation: generate_daily_batch(count=10, delay_minutes=30)
          - Generates 10 editions sequentially
          - Sleeps 30 minutes between starts (staggered, not parallel)
          - Returns list of generated edition IDs
        - Cleanup old: cleanup_old_editions(keep_days=30)
          - Deletes editions created >30 days ago
          - Clones directory cleanup (removes empty date folders)
          - Returns count of deleted editions
        - Cleanup excess: cleanup_excess_editions(max_editions=100)
          - Keeps only newest 100 editions (by created_at)
          - Deletes oldest first if count > 100
          - Returns count deleted (0 if under limit)
        - Edition structure: JSON with 5-page magazine (albums, descriptions, metadata)
        - Edition ID format: YYYY-MM-DD-NNN (e.g., "2026-02-07-001")
        - Storage: data/magazine-editions/{date}/{number}/edition.json
        - Caching: Pre-generated editions cached in frontend memory (used by /magazine/random)
        - Surprise feature: Frontend randomly selects from these pre-generated editions
        - Called by: APScheduler trigger at 03:00 UTC daily
        - Concurrent safety: Sequential (not parallel), safe with shared DB session
        - Idempotent: Safe to call multiple times (always generates new batch)
        - Long-running: Can take 15-60 minutes (caller aware of blocking time)
        
        Example Execution Timeline:
            # 03:00 UTC - Task starts
            # 03:10 - Edition 1 generated (finished)
            # 03:40 - Edition 2 generated (finished)
            # 04:10 - Edition 3 generated (finished)
            # ... (30-minute delays between each)
            # 05:40 - Edition 10 generated (finished)
            # 05:41 - Cleanup: Deleted 2 editions from Jan
            # 05:42 - Cleanup: No excess (85 editions < 100 max)
            # 05:42 - Task complete
            # Logs: "✅ Génération magazines terminée: 10 créées, 2 anciennes supprimées, 0 excédent supprimé"
        """
        logger.info("📰 Début génération lot de magazines")
        db = SessionLocal()
        
        try:
            edition_service = MagazineEditionService(db)
            
            # Générer 10 éditions avec 30 minutes d'intervalle
            generated_ids = await edition_service.generate_daily_batch(count=10, delay_minutes=30)
            
            # Nettoyer les éditions de plus de 30 jours
            deleted_count = edition_service.cleanup_old_editions(keep_days=30)
            
            # Nettoyer l'excédent si > 100 éditions
            excess_deleted = edition_service.cleanup_excess_editions(max_editions=100)
            
            logger.info(f"✅ Génération magazines terminée: {len(generated_ids)} créées, {deleted_count} anciennes supprimées, {excess_deleted} excédent supprimé")
            self._record_execution('generate_magazine_editions', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur génération magazines: {e}")
            self._record_execution('generate_magazine_editions', 'error', str(e))
        finally:
            db.close()
