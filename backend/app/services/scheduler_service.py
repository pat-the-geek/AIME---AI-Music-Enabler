"""Service de scheduler optimisé par IA pour tâches intelligentes."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from collections import Counter
import logging

from app.database import SessionLocal
from app.services.ai_service import AIService
from app.services.spotify_service import SpotifyService
from app.models import Album, Track, ListeningHistory, Metadata

logger = logging.getLogger(__name__)


class SchedulerService:
    """Scheduler intelligent avec optimisation par IA."""
    
    def __init__(self, config: dict):
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_executions = {}  # Tracking des dernières exécutions par tâche
        
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
        """Démarrer le scheduler."""
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
        
        self.scheduler.start()
        self.is_running = True
        logger.info("📅 Scheduler démarré avec tâches optimisées")
    
    async def stop(self):
        """Arrêter le scheduler."""
        if not self.is_running:
            logger.info("📅 Scheduler n'est pas en cours d'exécution")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("📅 Scheduler arrêté")
    
    def get_status(self) -> dict:
        """Obtenir le statut du scheduler."""
        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'last_execution': self.last_executions.get(job.id)
                })
        
        return {
            'running': self.is_running,
            'jobs': jobs,
            'job_count': len(jobs)
        }
    
    async def _daily_enrichment(self):
        """Enrichissement quotidien automatique."""
        self.last_executions['daily_enrichment'] = datetime.now(timezone.utc).isoformat()
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
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement quotidien: {e}")
        finally:
            db.close()
    
    async def _weekly_haiku(self):
        """Génération hebdomadaire de haïku."""
        self.last_executions['weekly_haiku'] = datetime.now(timezone.utc).isoformat()
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
            
        except Exception as e:
            logger.error(f"❌ Erreur génération haïku: {e}")
        finally:
            db.close()
    
    async def _monthly_analysis(self):
        """Analyse mensuelle des patterns."""
        self.last_executions['monthly_analysis'] = datetime.now(timezone.utc).isoformat()
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
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse mensuelle: {e}")
        finally:
            db.close()
    
    async def _optimize_ai_descriptions(self):
        """Optimiser les descriptions IA des albums populaires."""
        self.last_executions['optimize_ai_descriptions'] = datetime.now(timezone.utc).isoformat()
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
            
        except Exception as e:
            logger.error(f"❌ Erreur optimisation IA: {e}")
        finally:
            db.close()
    
    async def trigger_task(self, task_name: str) -> dict:
        """Déclencher manuellement une tâche."""
        tasks = {
            'daily_enrichment': self._daily_enrichment,
            'weekly_haiku': self._weekly_haiku,
            'monthly_analysis': self._monthly_analysis,
            'optimize_ai_descriptions': self._optimize_ai_descriptions
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
