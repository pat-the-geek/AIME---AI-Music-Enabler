"""Service de scheduler optimisé par IA pour tâches intelligentes."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
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
    
    def _record_execution(self, task_id: str, status: str = 'success', error: str = None):
        """Enregistrer l'exécution d'une tâche en base de données."""
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
        """Obtenir le statut du scheduler avec les exécutions depuis la DB."""
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
        """Enrichissement quotidien automatique."""
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
        """Génération hebdomadaire de haïku."""
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
        """Analyse mensuelle des patterns."""
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
        """Optimiser les descriptions IA des albums populaires."""
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
        """Générer haikus pour 5 albums - Format IDENTIQUE à l'API /collection/markdown/presentation."""
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
        """Exporter la collection complète en markdown avec le même format que l'API."""
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
        """Exporter la collection complète en JSON avec le même format que l'API."""
        logger.info("📊 Export collection en JSON")
        db = SessionLocal()
        
        try:
            # Récupérer tous les albums de collection Discogs, triés par titre
            albums = db.query(Album).filter(Album.source == 'discogs').order_by(Album.title).all()
            
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
        """Nettoyer les anciens fichiers en conservant seulement les N derniers de chaque type."""
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
        """Enrichir les albums importés en arrière-plan (Spotify + IA)."""
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
        """Synchronisation quotidienne de la collection Discogs."""
        logger.info("💿 Début synchronisation quotidienne Discogs")
        
        try:
            # Importer la fonction de sync depuis le API
            from app.api.v1.services import _sync_discogs_task
            
            # Exécuter la sync
            await _sync_discogs_task(limit=None)
            
            logger.info("✅ Synchronisation Discogs quotidienne terminée")
            self._record_execution('sync_discogs_daily', 'success')
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sync Discogs quotidienne: {e}")
            self._record_execution('sync_discogs_daily', 'error', str(e))
    
    async def trigger_task(self, task_name: str) -> dict:
        """Déclencher manuellement une tâche."""
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
        """Génération quotidienne de magazines pré-générés."""
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
