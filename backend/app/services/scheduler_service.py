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
from app.services.ai_service import AIService
from app.services.spotify_service import SpotifyService
from app.services.markdown_export_service import MarkdownExportService
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
            try:
                for job in self.scheduler.get_jobs():
                    try:
                        jobs.append({
                            'id': job.id,
                            'name': job.name,
                            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                            'last_execution': self.last_executions.get(job.id)
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
    
    async def _generate_random_haikus(self):
        """Générer haikus pour 5 albums aléatoires et exporter en markdown structuré."""
        import random
        
        self.last_executions['generate_haiku_scheduled'] = datetime.now(timezone.utc).isoformat()
        logger.info("🎋 Génération haikus pour 5 albums random")
        db = SessionLocal()
        
        try:
            # Récupérer 5 albums aléatoires
            all_albums = db.query(Album).all()
            if len(all_albums) < 5:
                logger.warning("Pas assez d'albums pour générer haikus")
                return
            
            selected_albums = random.sample(all_albums, 5)
            
            # Générer markdown structuré avec table des matières
            markdown_content = StringIO()
            markdown_content.write("# 🎋 Haikus Générés - Sélection Aléatoire\n\n")
            markdown_content.write(f"**Généré le:** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n")
            markdown_content.write(f"**Nombre de haikus:** {len(selected_albums)}\n\n")
            markdown_content.write("---\n\n")
            
            # Table des matières
            markdown_content.write("## Table des matières\n\n")
            for i, album in enumerate(selected_albums, 1):
                artist_name = album.artists[0].name if album.artists else "Artiste inconnu"
                album_anchor = f"{album.title.replace(' ', '-').lower()}"
                markdown_content.write(f"{i}. [{album.title} - {artist_name}](#{album_anchor})\n")
            
            markdown_content.write("\n---\n\n")
            
            # Générer haikus pour chaque album
            for i, album in enumerate(selected_albums, 1):
                artist_name = album.artists[0].name if album.artists else "Artiste inconnu"
                
                markdown_content.write(f"## {i}. {album.title}\n\n")
                markdown_content.write(f"**Artiste:** {artist_name}\n")
                
                if album.year:
                    markdown_content.write(f"- **Année:** {album.year}\n")
                if album.support:
                    markdown_content.write(f"- **Support:** {album.support}\n")
                if album.discogs_id:
                    markdown_content.write(f"- **Discogs ID:** {album.discogs_id}\n")
                
                markdown_content.write("\n")
                
                # Générer haiku
                haiku_data = {
                    'album_title': album.title,
                    'artist_name': artist_name,
                    'year': album.year or 'Année inconnue'
                }
                
                try:
                    haiku = await self.ai.generate_haiku(haiku_data)
                    markdown_content.write(f"```\n{haiku}\n```\n\n")
                except Exception as e:
                    logger.error(f"Erreur génération haiku pour {album.title}: {e}")
                    markdown_content.write(f"```\n[Haiku non disponible]\n```\n\n")
                
                # Liens
                links = []
                if album.spotify_url:
                    links.append(f"[Spotify]({album.spotify_url})")
                if album.discogs_url:
                    links.append(f"[Discogs]({album.discogs_url})")
                
                if links:
                    markdown_content.write("**Liens:** " + " | ".join(links) + "\n")
                
                # Image de couverture
                if album.images:
                    image_url = album.images[0].url
                    markdown_content.write(f"\n![{album.title}]({image_url})\n")
                
                markdown_content.write("\n---\n\n")
            
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
                f.write(markdown_content.getvalue())
            
            logger.info(f"✅ Haikus sauvegardés: {filepath}")
            
            # Nettoyer les anciens fichiers
            self._cleanup_old_files()
            
        except Exception as e:
            logger.error(f"❌ Erreur génération haikus: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()
    
    async def _export_collection_markdown(self):
        """Exporter la collection complète en markdown avec le même format que l'API."""
        self.last_executions['export_collection_markdown'] = datetime.now(timezone.utc).isoformat()
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
            
        except Exception as e:
            logger.error(f"❌ Erreur export markdown: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()
    
    async def _export_collection_json(self):
        """Exporter la collection complète en JSON avec le même format que l'API."""
        self.last_executions['export_collection_json'] = datetime.now(timezone.utc).isoformat()
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
            
        except Exception as e:
            logger.error(f"❌ Erreur export JSON: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
    
    async def trigger_task(self, task_name: str) -> dict:
        """Déclencher manuellement une tâche."""
        tasks = {
            'daily_enrichment': self._daily_enrichment,
            'generate_haiku_scheduled': self._generate_random_haikus,
            'export_collection_markdown': self._export_collection_markdown,
            'export_collection_json': self._export_collection_json,
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
