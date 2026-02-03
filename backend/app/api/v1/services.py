"""Routes API pour les services externes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
import logging

from app.database import get_db, SessionLocal
from app.core.config import get_settings
from app.services.tracker_service import TrackerService
from app.services.roon_tracker_service import RoonTrackerService
from app.services.roon_service import RoonService
from app.services.scheduler_service import SchedulerService
from app.services.discogs_service import DiscogsService
from app.services.spotify_service import SpotifyService
from app.services.ai_service import AIService
from app.services.lastfm_service import LastFMService
from app.models import Album, Artist, Image, Metadata, Track, ListeningHistory, ServiceState

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models pour les requêtes
class RoonConfigRequest(BaseModel):
    """Modèle pour la configuration Roon."""
    server: str


class RoonTestConnectionRequest(BaseModel):
    """Modèle pour tester la connexion Roon."""
    server: str

# Instances globales
_tracker_instance = None
_roon_tracker_instance = None
_scheduler_instance = None
_roon_service_instance = None  # Instance persistante pour maintenir la connexion

# Tracking des dernières exécutions manuelles
_last_executions = {
    'discogs_sync': None,
    'lastfm_import': None,
    'enrichment': None,
    'spotify_enrich': None
}


# ===== Helper Functions pour Persistance des États =====

def save_service_state(service_name: str, is_active: bool):
    """Sauvegarder l'état d'un service dans la DB."""
    db = SessionLocal()
    try:
        state = db.query(ServiceState).filter_by(service_name=service_name).first()
        if state is None:
            state = ServiceState(service_name=service_name)
            db.add(state)
        
        state.is_active = is_active
        state.last_updated = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"💾 État du service '{service_name}' sauvegardé: {'actif' if is_active else 'inactif'}")
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde état service '{service_name}': {e}")
        db.rollback()
    finally:
        db.close()


def get_service_state(service_name: str) -> bool:
    """Récupérer l'état d'un service depuis la DB."""
    db = SessionLocal()
    try:
        state = db.query(ServiceState).filter_by(service_name=service_name).first()
        return state.is_active if state else False
    except Exception as e:
        logger.error(f"❌ Erreur récupération état service '{service_name}': {e}")
        return False
    finally:
        db.close()


async def restore_active_services():
    """Restaurer automatiquement les services qui étaient actifs."""
    logger.info("🔄 Restauration des services actifs...")
    db = SessionLocal()
    try:
        # Récupérer tous les services actifs
        active_services = db.query(ServiceState).filter_by(is_active=True).all()
        
        for service_state in active_services:
            service_name = service_state.service_name
            try:
                if service_name == 'tracker':
                    tracker = get_tracker()
                    await tracker.start()
                    logger.info(f"✅ Tracker Last.fm restauré")
                elif service_name == 'roon_tracker':
                    # Pour Roon, attendre un peu plus que les zones soient disponibles
                    import asyncio
                    logger.info(f"⏳ Attente connexion Roon avant restauration du tracker...")
                    await asyncio.sleep(2)  # Donner 2s de plus à Roon pour se connecter
                    
                    roon_tracker = get_roon_tracker()
                    await roon_tracker.start()
                    logger.info(f"✅ Tracker Roon restauré")
                elif service_name == 'scheduler':
                    scheduler = get_scheduler()
                    await scheduler.start()
                    logger.info(f"✅ Scheduler restauré")
                else:
                    logger.warning(f"⚠️ Service inconnu: {service_name}")
            except Exception as e:
                logger.error(f"❌ Erreur restauration service '{service_name}': {e}")
        
        if not active_services:
            logger.info("ℹ️ Aucun service actif à restaurer")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la restauration des services: {e}")
    finally:
        db.close()


def get_tracker():
    """Obtenir l'instance du tracker Last.fm."""
    global _tracker_instance
    if _tracker_instance is None:
        settings = get_settings()
        # Fusionner secrets et app_config pour le tracker
        config = {**settings.secrets, **settings.app_config}
        _tracker_instance = TrackerService(config)
    return _tracker_instance


def get_roon_tracker():
    """Obtenir l'instance du tracker Roon."""
    global _roon_tracker_instance
    if _roon_tracker_instance is None:
        settings = get_settings()
        # Fusionner secrets et app_config pour le tracker Roon
        config = {**settings.secrets, **settings.app_config}
        # Passer l'instance Roon persistante au tracker
        roon_service = get_roon_service()
        _roon_tracker_instance = RoonTrackerService(config, roon_service=roon_service)
    return _roon_tracker_instance


def get_scheduler():
    """Obtenir l'instance du scheduler."""
    global _scheduler_instance
    if _scheduler_instance is None:
        settings = get_settings()
        # Fusionner secrets et app_config pour le scheduler
        config = {**settings.secrets, **settings.app_config}
        _scheduler_instance = SchedulerService(config)
    return _scheduler_instance


def get_roon_service():
    """Obtenir l'instance persistante du RoonService."""
    global _roon_service_instance
    settings = get_settings()
    roon_server = settings.app_config.get('roon_server')
    
    if not roon_server:
        return None
    
    # Si l'instance existe et que le serveur n'a pas changé, la retourner
    if _roon_service_instance is not None:
        if hasattr(_roon_service_instance, 'server') and _roon_service_instance.server == roon_server:
            return _roon_service_instance
    
    # Callback pour sauvegarder le token quand il est reçu
    def save_token(token: str):
        settings.app_config['roon_token'] = token
        settings.save_app_config()
        logger.info(f"💾 Token Roon sauvegardé dans la configuration")
    
    # Créer une nouvelle instance avec le nouveau serveur et le callback de sauvegarde
    roon_token = settings.app_config.get('roon_token')
    _roon_service_instance = RoonService(server=roon_server, token=roon_token, on_token_received=save_token)
    return _roon_service_instance


@router.get("/tracker/status")
async def get_tracker_status():
    """Statut du tracker Last.fm."""
    tracker = get_tracker()
    return tracker.get_status()


@router.get("/status/all")
async def get_all_services_status():
    """Récupérer le statut de tous les services avec leurs dernières activités."""
    tracker = get_tracker()
    roon_tracker = get_roon_tracker()
    scheduler = get_scheduler()
    
    return {
        "tracker": tracker.get_status(),
        "roon_tracker": roon_tracker.get_status(),
        "scheduler": scheduler.get_status(),
        "manual_operations": _last_executions
    }


@router.get("/roon-tracker/status")
async def get_roon_tracker_status():
    """Statut du tracker Roon."""
    tracker = get_roon_tracker()
    return tracker.get_status()


@router.post("/roon-tracker/start")
async def start_roon_tracker():
    """Démarrer le tracker Roon."""
    tracker = get_roon_tracker()
    await tracker.start()
    save_service_state('roon_tracker', True)
    return {"status": "started"}


@router.post("/roon-tracker/stop")
async def stop_roon_tracker():
    """Arrêter le tracker Roon."""
    tracker = get_roon_tracker()
    await tracker.stop()
    save_service_state('roon_tracker', False)
    return {"status": "stopped"}


@router.get("/roon/config")
async def get_roon_config():
    """Récupérer la configuration Roon actuelle."""
    settings = get_settings()
    return {
        "server": settings.app_config.get("roon_server", ""),
        "configured": bool(settings.app_config.get("roon_server"))
    }


@router.post("/roon/config")
async def save_roon_config(request: RoonConfigRequest):
    """Sauvegarder la configuration Roon."""
    settings = get_settings()
    
    # Valider l'adresse
    if not request.server or not request.server.strip():
        raise HTTPException(status_code=400, detail="L'adresse du serveur ne peut pas être vide")
    
    # Sauvegarder dans app.json
    settings.app_config["roon_server"] = request.server.strip()
    settings.save_app_config()
    
    # Réinitialiser les instances pour qu'elles utilisent la nouvelle config
    global _roon_tracker_instance, _roon_service_instance
    _roon_tracker_instance = None
    _roon_service_instance = None
    
    # Initialiser immédiatement le service pour que Roon détecte l'extension
    roon_service = get_roon_service()
    
    if roon_service and roon_service.is_connected():
        return {
            "status": "success",
            "server": request.server.strip(),
            "connected": True,
            "message": "Configuration sauvegardée. L'extension devrait maintenant apparaître dans Roon → Settings → Extensions."
        }
    else:
        return {
            "status": "success",
            "server": request.server.strip(),
            "connected": False,
            "message": "Configuration sauvegardée mais impossible de se connecter. Vérifiez l'adresse et assurez-vous que Roon Core est démarré."
        }


@router.get("/roon/status")
async def get_roon_status():
    """Récupérer le statut de la connexion Roon."""
    settings = get_settings()
    roon_server = settings.app_config.get('roon_server')
    
    if not roon_server:
        return {
            "configured": False,
            "connected": False,
            "message": "Aucun serveur Roon configuré"
        }
    
    roon_service = get_roon_service()
    
    if not roon_service or not roon_service.is_connected():
        return {
            "configured": True,
            "connected": False,
            "server": roon_server,
            "message": "Impossible de se connecter au serveur Roon"
        }
    
    # Vérifier si on a un token (= extension autorisée)
    token = roon_service.get_token()
    zones = roon_service.get_zones()
    
    return {
        "configured": True,
        "connected": True,
        "authorized": token is not None,
        "server": roon_server,
        "zones_count": len(zones),
        "message": "Connecté et autorisé" if token else "Connecté mais en attente d'autorisation dans Roon"
    }


@router.post("/roon/test-connection")
async def test_roon_connection(request: RoonTestConnectionRequest):
    """Tester la connexion à un serveur Roon."""
    if not request.server or not request.server.strip():
        raise HTTPException(status_code=400, detail="L'adresse du serveur ne peut pas être vide")
    
    try:
        # Créer une instance temporaire du service Roon
        roon_service = RoonService(server=request.server.strip())
        
        # Vérifier si la connexion est établie
        if roon_service.roon_api is None:
            return {
                "connected": False,
                "error": "Impossible de se connecter au serveur Roon. Vérifiez l'adresse et assurez-vous que Roon Core est démarré."
            }
        
        # Récupérer les zones disponibles
        zones_count = len(roon_service.zones) if hasattr(roon_service, 'zones') else 0
        
        return {
            "connected": True,
            "zones_found": zones_count,
            "message": f"Connexion réussie ! {zones_count} zone(s) détectée(s). Cliquez sur 'Enregistrer' pour activer l'extension."
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


@router.post("/tracker/start")
async def start_tracker():
    """Démarrer le tracker Last.fm."""
    tracker = get_tracker()
    await tracker.start()
    save_service_state('tracker', True)
    return {"status": "started"}


@router.post("/tracker/stop")
async def stop_tracker():
    """Arrêter le tracker Last.fm."""
    tracker = get_tracker()
    await tracker.stop()
    save_service_state('tracker', False)
    return {"status": "stopped"}


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Statut du scheduler de tâches optimisées."""
    scheduler = get_scheduler()
    return scheduler.get_status()


@router.get("/scheduler/config")
async def get_scheduler_config():
    """Configuration des tâches du scheduler."""
    settings = get_settings()
    scheduler_config = settings.app_config.get('scheduler', {})
    return {
        'enabled': scheduler_config.get('enabled', True),
        'output_dir': scheduler_config.get('output_dir', 'Scheduled Output'),
        'max_files_per_type': scheduler_config.get('max_files_per_type', 5),
        'tasks': scheduler_config.get('tasks', [])
    }


@router.patch("/scheduler/config")
async def update_scheduler_config(max_files_per_type: int = None):
    """Mettre à jour la configuration du scheduler.
    
    Args:
        max_files_per_type: Nombre maximum de fichiers à conserver par type
    """
    settings = get_settings()
    
    if max_files_per_type is not None:
        if max_files_per_type < 1:
            raise HTTPException(status_code=400, detail="max_files_per_type doit être >= 1")
        
        settings.app_config['scheduler']['max_files_per_type'] = max_files_per_type
        logger.info(f"✅ Configuration mise à jour: max_files_per_type={max_files_per_type}")
    
    return {
        'max_files_per_type': settings.app_config['scheduler'].get('max_files_per_type', 5)
    }


@router.post("/scheduler/start")
async def start_scheduler():
    """Démarrer le scheduler de tâches optimisées."""
    scheduler = get_scheduler()
    await scheduler.start()
    save_service_state('scheduler', True)
    return {"status": "started"}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Arrêter le scheduler de tâches optimisées."""
    scheduler = get_scheduler()
    await scheduler.stop()
    save_service_state('scheduler', False)
    return {"status": "stopped"}


@router.post("/scheduler/trigger/{task_name}")
async def trigger_scheduler_task(task_name: str):
    """Déclencher manuellement une tâche planifiée.
    
    Tasks disponibles:
    - daily_enrichment: Enrichissement quotidien (50 albums)
    - generate_haiku_scheduled: Génération haikus pour 5 albums aléatoires
    - export_collection_markdown: Export collection en markdown
    - export_collection_json: Export collection en JSON
    - weekly_haiku: Génération de haïku hebdomadaire
    - monthly_analysis: Analyse mensuelle des patterns
    - optimize_ai_descriptions: Optimiser descriptions IA des albums populaires
    """
    scheduler = get_scheduler()
    try:
        result = await scheduler.trigger_task(task_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scheduler/optimization-results")
async def get_optimization_results():
    """Récupérer les résultats d'optimisation IA du scheduler.
    
    Retourne les données d'optimisation du fichier config/OPTIMIZATION-RESULTS.json
    """
    import json
    import os
    from pathlib import Path
    
    # Remonter depuis backend/app/api/v1/services.py vers la racine du projet
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent.parent
    results_file = project_root / 'config' / 'OPTIMIZATION-RESULTS.json'
    
    if not results_file.exists():
        return {
            "status": "NOT_AVAILABLE",
            "message": "Les résultats d'optimisation ne sont pas encore disponibles"
        }
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors de la lecture des résultats d'optimisation: {e}")
        raise HTTPException(status_code=500, detail="Impossible de lire les résultats d'optimisation")


# Variable globale pour stocker la progression
_sync_progress = {
    "status": "idle",
    "current": 0,
    "total": 0,
    "current_album": "",
    "synced": 0,
    "skipped": 0,
    "errors": 0
}

# État de l'importation Last.fm
_lastfm_import_progress = {
    "status": "idle",
    "current_batch": 0,
    "total_batches": 0,
    "imported": 0,
    "skipped": 0,
    "errors": 0,
    "total_scrobbles": 0
}

@router.get("/discogs/sync/progress")
async def get_sync_progress():
    """Obtenir la progression de la synchronisation."""
    return _sync_progress

@router.get("/lastfm/import/progress")
async def get_lastfm_import_progress():
    """Obtenir la progression de l'importation Last.fm."""
    return _lastfm_import_progress

@router.post("/lastfm/clean-duplicates")
async def clean_lastfm_duplicates(db: Session = Depends(get_db)):
    """Nettoyer les doublons dans l'historique d'écoute Last.fm.
    
    Utilise la règle des 10 minutes: si le même track a été écouté il y a moins de 10 minutes,
    c'est un doublon (bug Last.fm). Garde seulement la première occurrence.
    """
    from sqlalchemy import func
    
    try:
        logger.info("🔍 Début nettoyage des doublons Last.fm...")
        
        # Compter les entrées initiales
        total_initial = db.query(ListeningHistory).count()
        logger.info(f"📊 Total initial: {total_initial} entrées")
        
        # Chercher les tracks avec plusieurs entrées
        duplicates = db.query(
            ListeningHistory.track_id,
            func.count(ListeningHistory.id).label('count'),
            func.min(ListeningHistory.timestamp).label('min_ts'),
            func.max(ListeningHistory.timestamp).label('max_ts')
        ).group_by(
            ListeningHistory.track_id
        ).having(
            func.count(ListeningHistory.id) > 1
        ).all()
        
        logger.info(f"📀 Tracks avec doublons potentiels: {len(duplicates)}")
        
        duplicates_deleted = 0
        
        # Pour chaque track avec doublons
        for track_id, count, min_ts, max_ts in duplicates:
            time_diff = abs(max_ts - min_ts)
            
            # Si tous les timestamps sont dans une fenêtre de 10 minutes
            if time_diff < 600:
                # Récupérer toutes les entrées et garder seulement la première
                entries = db.query(ListeningHistory).filter_by(
                    track_id=track_id
                ).order_by(ListeningHistory.timestamp).all()
                
                # Marquer les entrées 2+ pour suppression
                for entry in entries[1:]:
                    db.delete(entry)
                    duplicates_deleted += 1
        
        if duplicates_deleted > 0:
            logger.info(f"🗑️ Suppression de {duplicates_deleted} doublons...")
            db.commit()
            logger.info(f"✅ {duplicates_deleted} doublons supprimés")
        else:
            logger.info(f"✅ Aucun doublon trouvé!")
        
        # Compter les entrées finales
        total_final = db.query(ListeningHistory).count()
        logger.info(f"📊 Total final: {total_final} entrées")
        
        return {
            "status": "success",
            "total_initial": total_initial,
            "duplicates_deleted": duplicates_deleted,
            "total_final": total_final,
            "removed_entries": total_initial - total_final
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur nettoyage: {str(e)}")

@router.post("/discogs/sync")
async def sync_discogs_collection(
    background_tasks: BackgroundTasks,
    limit: int = None,
    db: Session = Depends(get_db)
):
    """Synchroniser la collection Discogs en arrière-plan.
    
    Args:
        limit: Nombre maximum d'albums à synchroniser (optionnel, pour tests)
    """
    global _sync_progress
    
    # Vérifier si une sync est déjà en cours
    if _sync_progress["status"] == "running":
        raise HTTPException(status_code=409, detail="Une synchronisation est déjà en cours")
    
    # Initialiser la progression
    _sync_progress = {
        "status": "starting",
        "current": 0,
        "total": 0,
        "current_album": "",
        "synced": 0,
        "skipped": 0,
        "errors": 0
    }
    
    # Lancer la synchronisation en arrière-plan
    background_tasks.add_task(_sync_discogs_task, limit)
    
    return {
        "status": "started",
        "message": "Synchronisation démarrée en arrière-plan"
    }

async def _sync_discogs_task(limit: int = None):
    """Tâche de synchronisation Discogs en arrière-plan."""
    global _last_executions, _sync_progress
    import logging
    logger = logging.getLogger(__name__)
    
    db = SessionLocal()
    
    try:
        # Enregistrer le début de l'opération
        _last_executions['discogs_sync'] = datetime.now(timezone.utc).isoformat()
        _sync_progress["status"] = "running"
        
        logger.info("🔄 Début synchronisation Discogs")
        settings = get_settings()
        secrets = settings.secrets
        discogs_config = secrets.get('discogs', {})
        spotify_config = secrets.get('spotify', {})
        ai_config = secrets.get('euria', {})
        
        discogs_service = DiscogsService(
            api_key=discogs_config.get('api_key'),
            username=discogs_config.get('username')
        )
        
        # Initialiser les services Spotify et IA
        spotify_service = SpotifyService(
            client_id=spotify_config.get('client_id'),
            client_secret=spotify_config.get('client_secret')
        )
        
        ai_service = AIService(
            url=ai_config.get('url'),
            bearer=ai_config.get('bearer')
        )
        
        _sync_progress["current_album"] = "Récupération de la collection..."
        logger.info("📡 Récupération collection Discogs...")
        albums_data = discogs_service.get_collection(limit=limit)
        logger.info(f"✅ {len(albums_data)} albums récupérés de Discogs")
        
        _sync_progress["total"] = len(albums_data)
        _sync_progress["current_album"] = "Début de l'import..."
        
        synced_count = 0
        skipped_count = 0
        error_count = 0
        
        for idx, album_data in enumerate(albums_data, 1):
            try:
                # Mettre à jour la progression
                _sync_progress["current"] = idx
                _sync_progress["current_album"] = f"{album_data.get('title', 'Unknown')} - {album_data.get('artists', ['Unknown'])[0]}"
                _sync_progress["synced"] = synced_count
                _sync_progress["skipped"] = skipped_count
                _sync_progress["errors"] = error_count
                
                # Vérifier si l'album existe déjà
                existing = db.query(Album).filter_by(
                    discogs_id=str(album_data['release_id'])
                ).first()
                
                if existing:
                    skipped_count += 1
                    _sync_progress["skipped"] = skipped_count
                    continue
                
                # Créer/récupérer artistes (dédoublonner pour éviter UNIQUE constraint)
                artists = []
                seen_artist_ids = set()
                
                for artist_name in album_data['artists']:
                    if not artist_name or not artist_name.strip():
                        continue
                    
                    artist = db.query(Artist).filter_by(name=artist_name).first()
                    if not artist:
                        artist = Artist(name=artist_name)
                        db.add(artist)
                        db.flush()
                    
                    # Éviter les doublons d'artistes (certains albums Discogs ont des duplicatas)
                    if artist.id not in seen_artist_ids:
                        artists.append(artist)
                        seen_artist_ids.add(artist.id)
                
                # Si pas d'artiste, ignorer cet album
                if not artists:
                    logger.warning(f"⚠️ Album sans artiste ignoré: {album_data.get('title', 'Unknown')}")
                    error_count += 1
                    continue
                
                # Déterminer le support
                support = "Unknown"
                if album_data.get('formats'):
                    format_name = album_data['formats'][0]
                    if 'Vinyl' in format_name or 'LP' in format_name:
                        support = "Vinyle"
                    elif 'CD' in format_name:
                        support = "CD"
                    elif 'Digital' in format_name:
                        support = "Digital"
                
                # Normaliser l'année (Discogs peut retourner 0 ou None)
                year = album_data.get('year')
                if year == 0:
                    year = None
                
                # Rechercher URL Spotify
                spotify_url = None
                try:
                    artist_name = album_data['artists'][0] if album_data['artists'] else ""
                    spotify_url = await spotify_service.search_album_url(artist_name, album_data['title'])
                    if spotify_url:
                        logger.info(f"🎵 Spotify trouvé pour: {album_data['title']}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur recherche Spotify pour {album_data['title']}: {e}")
                
                # Créer album
                album = Album(
                    title=album_data['title'],
                    year=year,
                    support=support,
                    source='discogs',  # Marquer comme album de collection Discogs
                    discogs_id=str(album_data['release_id']),
                    discogs_url=album_data.get('discogs_url'),
                    spotify_url=spotify_url
                )
                album.artists = artists
                db.add(album)
                db.flush()
                
                # Ajouter image
                if album_data.get('cover_image'):
                    image = Image(
                        url=album_data['cover_image'],
                        image_type='album',
                        source='discogs',
                        album_id=album.id
                    )
                    db.add(image)
                
                # Générer description IA avec délai pour éviter rate limiting
                ai_info = None
                try:
                    import asyncio
                    # Petit délai pour éviter de saturer l'API EurIA
                    await asyncio.sleep(0.3)
                    
                    artist_name = album_data['artists'][0] if album_data['artists'] else ""
                    ai_info = await ai_service.generate_album_info(artist_name, album_data['title'])
                    if ai_info:
                        logger.info(f"🤖 Description IA générée pour: {album_data['title']}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur génération IA pour {album_data['title']}: {e}")
                
                # Ajouter métadonnées
                metadata = Metadata(
                    album_id=album.id,
                    labels=','.join(album_data['labels']) if album_data.get('labels') else None,
                    ai_info=ai_info
                )
                db.add(metadata)
                
                synced_count += 1
                _sync_progress["synced"] = synced_count
                
                # Commit tous les 10 albums pour éviter les transactions trop longues
                if synced_count % 10 == 0:
                    db.commit()
                    logger.info(f"💾 {synced_count} albums sauvegardés...")
                
            except Exception as e:
                logger.error(f"❌ Erreur import album {album_data.get('title', 'Unknown')}: {e}")
                error_count += 1
                _sync_progress["errors"] = error_count
                db.rollback()  # Rollback pour cet album uniquement
                continue
        
        # Commit final
        db.commit()
        logger.info(f"✅ Synchronisation terminée: {synced_count} albums ajoutés, {skipped_count} ignorés, {error_count} erreurs")
        
        # Marquer comme terminé
        _sync_progress["status"] = "completed"
        _sync_progress["current_album"] = "Terminé !"
        
    except Exception as e:
        logger.error(f"❌ Erreur synchronisation Discogs: {e}")
        _sync_progress["status"] = "error"
        _sync_progress["current_album"] = f"Erreur: {str(e)}"
        db.rollback()
    finally:
        db.close()


@router.post("/ai/generate-info")
async def generate_ai_info(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Générer description IA pour un album."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    # Récupérer le service IA
    settings = get_settings()
    secrets = settings.secrets
    euria_config = secrets.get('euria', {})
    
    ai_service = AIService(
        url=euria_config.get('url'),
        bearer=euria_config.get('bearer'),
        max_attempts=euria_config.get('max_attempts', 5)
    )
    
    # Générer l'info
    artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
    artist_name = ', '.join(artists)
    
    ai_info = await ai_service.generate_album_info(artist_name, album.title)
    
    if not ai_info:
        raise HTTPException(status_code=500, detail="Erreur génération info IA")
    
    # Sauvegarder
    if not album.album_metadata:
        metadata = Metadata(album_id=album.id, ai_info=ai_info)
        db.add(metadata)
    else:
        album.album_metadata.ai_info = ai_info
    
    db.commit()
    
    return {
        "album_id": album_id,
        "ai_info": ai_info
    }


@router.post("/ai/enrich-all")
async def enrich_all_albums(
    limit: int = 10,  # Limiter à 10 albums par défaut pour éviter rate limiting
    db: Session = Depends(get_db)
):
    """Enrichir tous les albums avec Spotify et IA."""
    global _last_executions
    import logging
    import asyncio
    logger = logging.getLogger(__name__)
    
    # Enregistrer le début de l'opération
    _last_executions['enrichment'] = datetime.now(timezone.utc).isoformat()
    
    logger.info(f"🔄 Début enrichissement de {limit} albums")
    settings = get_settings()
    secrets = settings.secrets
    
    spotify_config = secrets.get('spotify', {})
    ai_config = secrets.get('euria', {})
    
    spotify_service = SpotifyService(
        client_id=spotify_config.get('client_id'),
        client_secret=spotify_config.get('client_secret')
    )
    
    ai_service = AIService(
        url=ai_config.get('url'),
        bearer=ai_config.get('bearer')
    )
    
    try:
        # Récupérer UNIQUEMENT les albums sans ai_info (ignorant spotify_url)
        # On enrichit d'abord l'IA pour tous, puis Spotify sera fait séparément
        albums = db.query(Album).options(joinedload(Album.album_metadata)).outerjoin(
            Metadata, Album.id == Metadata.album_id
        ).filter(
            (Metadata.id == None) | (Metadata.ai_info == None)
        ).limit(limit).all()
        
        logger.info(f"📀 {len(albums)} albums à enrichir")
        
        spotify_added = 0
        ai_added = 0
        errors = 0
        
        for album in albums:
            try:
                updated = False
                artist_name = album.artists[0].name if album.artists else ""
                
                logger.info(f"📀 Traitement: {album.title} (ID:{album.id}) - Spotify:{album.spotify_url is not None} Meta:{album.album_metadata is not None} AI:{album.album_metadata.ai_info if album.album_metadata else None}")
                
                # Enrichir Spotify si manquant
                if not album.spotify_url:
                    try:
                        spotify_url = await spotify_service.search_album_url(artist_name, album.title)
                        if spotify_url:
                            album.spotify_url = spotify_url
                            spotify_added += 1
                            updated = True
                            logger.info(f"🎵 Spotify ajouté: {album.title}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur Spotify pour {album.title}: {e}")
                
                # Enrichir IA si manquant - délai pour éviter rate limit
                if not album.album_metadata or not album.album_metadata.ai_info:
                    try:
                        await asyncio.sleep(1.0)  # Délai de 1s entre appels IA (2000 chars = plus long)
                        ai_info = await ai_service.generate_album_info(artist_name, album.title)
                        if ai_info:
                            if not album.album_metadata:
                                metadata = Metadata(album_id=album.id, ai_info=ai_info)
                                db.add(metadata)
                            else:
                                album.album_metadata.ai_info = ai_info
                            ai_added += 1
                            updated = True
                            logger.info(f"🤖 IA ajoutée: {album.title}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur IA pour {album.title}: {e}")
                
                if updated:
                    db.commit()
                    
            except Exception as e:
                logger.error(f"❌ Erreur enrichissement {album.title}: {e}")
                db.rollback()
                errors += 1
                continue
        
        logger.info(f"✅ Enrichissement terminé: {spotify_added} Spotify, {ai_added} IA, {errors} erreurs")
        
        return {
            "status": "success",
            "albums_processed": len(albums),
            "spotify_added": spotify_added,
            "ai_added": ai_added,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur enrichissement: {str(e)}")


@router.post("/ai/enrich-album/{album_id}")
async def enrich_single_album(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Enrichir un album spécifique avec images, Spotify, et IA."""
    import logging
    import asyncio
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔄 Enrichissement de l'album {album_id}")
        settings = get_settings()
        secrets = settings.secrets
        
        # Récupérer l'album
        album = db.query(Album).filter(Album.id == album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album non trouvé")
        
        updated = False
        enrichment_details = {
            "spotify_url": None,
            "images": False,
            "ai_description": False
        }
        
        # 1. Enrichir avec Spotify
        try:
            logger.info(f"🔍 Recherche Spotify pour {album.title}")
            spotify_service = SpotifyService(
                client_id=secrets.get('spotify', {}).get('client_id', ''),
                client_secret=secrets.get('spotify', {}).get('client_secret', '')
            )
            
            artist_name = album.artists[0].name if album.artists else ''
            logger.info(f"🔍 Recherche: artist={artist_name}, album={album.title}")
            spotify_details = await spotify_service.search_album_details(artist_name, album.title)
            logger.info(f"📊 Résultat Spotify: {spotify_details}")
            
            if spotify_details:
                # Mettre à jour l'URL Spotify
                album.spotify_url = spotify_details.get('spotify_url')
                enrichment_details["spotify_url"] = album.spotify_url
                updated = True
                logger.info(f"✨ URL Spotify trouvée: {album.spotify_url}")
                
                # Mettre à jour l'année si elle est disponible
                if spotify_details.get('year'):
                    album.year = spotify_details.get('year')
                    updated = True
                    logger.info(f"📅 Année Spotify trouvée: {album.year}")
                
                # Mettre à jour les images (forcer la mise à jour même si elles existent)
                image_url = spotify_details.get('image_url')
                logger.info(f"🎨 Image URL depuis Spotify: {image_url}")
                if image_url:
                    # Supprimer les anciennes images
                    db.query(Image).filter(Image.album_id == album.id).delete()
                    
                    # Ajouter la nouvelle image
                    image = Image(
                        album_id=album.id,
                        url=image_url,
                        image_type='album',
                        source='spotify'
                    )
                    db.add(image)
                    enrichment_details["images"] = True
                    updated = True
                    logger.info(f"🖼️ Image Spotify ajoutée/mise à jour: {image_url}")
                else:
                    logger.warning(f"⚠️ Pas d'image trouvée dans les détails Spotify")
        except Exception as e:
            logger.warning(f"⚠️ Erreur Spotify pour {album.title}: {e}")
        
        # 2. Enrichir avec IA (descriptions) - de façon optionnelle sans bloquer
        try:
            from app.services.ai_service import AIService
            ai_service = AIService(
                url=secrets.get('euria', {}).get('url', ''),
                bearer=secrets.get('euria', {}).get('bearer', '')
            )
            
            artist_name = album.artists[0].name if album.artists else 'Unknown'
            try:
                # Ajouter un timeout pour l'IA pour ne pas bloquer
                ai_info = await asyncio.wait_for(
                    ai_service.generate_album_info(artist_name, album.title),
                    timeout=10
                )
                
                if ai_info:
                    if not album.album_metadata:
                        metadata = Metadata(album_id=album.id, ai_info=ai_info)
                        db.add(metadata)
                    else:
                        album.album_metadata.ai_info = ai_info
                    enrichment_details["ai_description"] = True
                    updated = True
                    logger.info(f"🤖 Description IA ajoutée")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout IA pour {album.title}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur IA pour {album.title}: {e}")
        
        # Sauvegarder les modifications
        if updated:
            db.commit()
            logger.info(f"✅ Album {album.title} enrichi avec succès - Spotify OK")
        else:
            logger.warning(f"⚠️ Album {album.title} - aucun enrichissement appliqué")
        
        return {
            "status": "success",
            "album_id": album_id,
            "album_title": album.title,
            "enrichment_details": enrichment_details,
            "message": f"Album enrichi avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement album {album_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur enrichissement: {str(e)}")


@router.post("/spotify/enrich-all")
async def enrich_spotify_urls(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Enrichir les URLs Spotify et années manquantes.
    
    Args:
        limit: Nombre d'albums à traiter (0 = tous les albums sans limite)
    """
    global _last_executions
    import logging
    import asyncio
    logger = logging.getLogger(__name__)
    
    # Enregistrer le début de l'opération
    _last_executions['spotify_enrich'] = datetime.now(timezone.utc).isoformat()
    
    logger.info(f"🎵 Début enrichissement Spotify de {limit if limit > 0 else 'TOUS les'} albums")
    settings = get_settings()
    secrets = settings.secrets
    
    spotify_config = secrets.get('spotify', {})
    
    spotify_service = SpotifyService(
        client_id=spotify_config.get('client_id'),
        client_secret=spotify_config.get('client_secret')
    )
    
    try:
        # Récupérer les albums sans spotify_url ou sans année
        query = db.query(Album).filter((Album.spotify_url == None) | (Album.year == None))
        if limit > 0:
            albums = query.limit(limit).all()
        else:
            albums = query.all()
        
        logger.info(f"📀 {len(albums)} albums à enrichir")
        
        spotify_added = 0
        year_added = 0
        errors = 0
        
        for idx, album in enumerate(albums, 1):
            try:
                artist_name = album.artists[0].name if album.artists else ""
                
                if idx % 10 == 0:
                    logger.info(f"📊 Progress: {idx}/{len(albums)}")
                
                # Enrichir avec détails Spotify (URL + année)
                spotify_details = await spotify_service.search_album_details(artist_name, album.title)
                if spotify_details:
                    if not album.spotify_url and spotify_details.get("spotify_url"):
                        album.spotify_url = spotify_details["spotify_url"]
                        spotify_added += 1
                    if not album.year and spotify_details.get("year"):
                        album.year = spotify_details["year"]
                        year_added += 1
                    
                    db.commit()
                    logger.info(f"🎵 [{idx}/{len(albums)}] {album.title} enrichi (URL: {bool(spotify_details.get('spotify_url'))}, Année: {spotify_details.get('year')})")
                else:
                    logger.warning(f"⚠️ [{idx}/{len(albums)}] Spotify non trouvé pour {album.title}")
                
                # Petit délai pour éviter rate limiting
                if idx % 10 == 0:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"❌ Erreur Spotify pour {album.title}: {e}")
                db.rollback()
                errors += 1
                continue
        
        logger.info(f"✅ Enrichissement terminé: {spotify_added} URLs ajoutées, {year_added} années ajoutées, {errors} erreurs")
        
        return {
            "status": "success",
            "albums_processed": len(albums),
            "spotify_added": spotify_added,
            "year_added": year_added,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement Spotify: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur enrichissement Spotify: {str(e)}")


@router.post("/lastfm/import-history")
async def import_lastfm_history(
    limit: Optional[int] = None,
    skip_existing: bool = True,
    db: Session = Depends(get_db)
):
    """Importer l'historique d'écoute COMPLET depuis Last.fm.
    
    Args:
        limit: Nombre maximum de tracks à importer (None = tout importer, le défaut)
        skip_existing: Ignorer les tracks déjà en base (False) ou tout réimporter (True)
    """
    global _last_executions, _lastfm_import_progress
    import logging
    import asyncio
    from collections import defaultdict
    logger = logging.getLogger(__name__)
    
    # Initialiser la progression
    _lastfm_import_progress = {
        "status": "starting",
        "current_batch": 0,
        "total_batches": 0,
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "total_scrobbles": 0
    }
    
    # Enregistrer le début de l'opération
    _last_executions['lastfm_import'] = datetime.now(timezone.utc).isoformat()
    
    if limit is None:
        logger.info(f"🔄 Début import COMPLET historique Last.fm (tous les scrobbles)")
    else:
        logger.info(f"🔄 Début import historique Last.fm (limit={limit})")
    
    settings = get_settings()
    secrets = settings.secrets
    
    lastfm_config = secrets.get('lastfm', {})
    spotify_config = secrets.get('spotify', {})
    ai_config = secrets.get('euria', {})
    
    lastfm_service = LastFMService(
        api_key=lastfm_config.get('api_key'),
        api_secret=lastfm_config.get('api_secret'),
        username=lastfm_config.get('username')
    )
    
    spotify_service = SpotifyService(
        client_id=spotify_config.get('client_id'),
        client_secret=spotify_config.get('client_secret')
    )
    
    ai_service = AIService(
        url=ai_config.get('url'),
        bearer=ai_config.get('bearer')
    )
    
    try:
        _lastfm_import_progress["status"] = "running"
        
        # Récupérer le nombre total de scrobbles
        total_scrobbles = lastfm_service.get_total_scrobbles()
        logger.info(f"📊 Total scrobbles utilisateur: {total_scrobbles}")
        _lastfm_import_progress["total_scrobbles"] = total_scrobbles
        
        # Récupérer l'historique par batches (Last.fm limite à 200 par requête)
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        # Tracking des derniers tracks importés par track_id pour la règle des 10 minutes
        last_import_by_track = {}  # {track_id: (timestamp, entry_id)}
        
        # Calcul du nombre de batches nécessaires
        batch_size = 200
        # Si limit est None, on veut ALL les scrobbles, donc on calcule le nombre de batches nécessaire
        # Si limit est fourni, on ne fetch que jusqu'à cette limite
        if limit is None:
            num_batches = (total_scrobbles // batch_size) + (1 if total_scrobbles % batch_size > 0 else 0)
            logger.info(f"📦 {num_batches} batches à traiter pour récupérer TOUS les {total_scrobbles} scrobbles")
        else:
            num_batches = (limit // batch_size) + 1
            logger.info(f"📦 {num_batches} batches à traiter (max {limit} tracks)")
        
        _lastfm_import_progress["total_batches"] = num_batches
        
        # Dictionnaire pour accumuler les albums à enrichir (évite doublons)
        albums_to_enrich = defaultdict(dict)
        
        # Set pour tracker les (track_id, timestamp) vus dans la session actuelle
        # Évite les doublons créés dans une même boucle avant commit
        seen_entries = set()
        
        for batch_num in range(num_batches):
            try:
                # Mettre à jour la progression
                _lastfm_import_progress["current_batch"] = batch_num + 1
                _lastfm_import_progress["imported"] = imported_count
                _lastfm_import_progress["skipped"] = skipped_count
                _lastfm_import_progress["errors"] = error_count
                
                # Récupérer batch de tracks avec pagination (page = batch_num + 1)
                if limit is None:
                    batch_limit = batch_size
                else:
                    batch_limit = min(batch_size, limit - imported_count - skipped_count)
                    if batch_limit <= 0:
                        break
                
                page_num = batch_num + 1
                logger.info(f"📥 Batch {batch_num + 1}/{num_batches} (Page {page_num})...")
                tracks = lastfm_service.get_user_history(limit=batch_limit, page=page_num)
                
                if not tracks:
                    logger.warning(f"⚠️ Aucun track dans le batch {batch_num + 1}")
                    break
                
                for track_data in tracks:
                    try:
                        artist_name = track_data['artist']
                        track_title = track_data['title']
                        album_title = track_data['album']
                        timestamp = track_data['timestamp']
                        
                        # Créer/récupérer artiste d'abord
                        artist = db.query(Artist).filter_by(name=artist_name).first()
                        if not artist:
                            artist = Artist(name=artist_name)
                            db.add(artist)
                            db.flush()
                        
                        # Chercher album par titre SEUL (pas filtrer par artiste!)
                        # Car un album peut avoir plusieurs artistes, on ne doit pas le dédupliquer par artiste principal
                        album = db.query(Album).filter_by(title=album_title).first()
                        
                        if not album:
                            album = Album(title=album_title)
                            db.add(album)
                            db.flush()
                        
                        # Vérifier que l'artiste est associé à l'album (sinon l'ajouter)
                        if artist not in album.artists:
                            album.artists.append(artist)
                        
                        # Créer/récupérer track pour avoir le track_id
                        track = db.query(Track).filter_by(
                            album_id=album.id,
                            title=track_title
                        ).first()
                        
                        if not track:
                            track = Track(
                                album_id=album.id,
                                title=track_title
                            )
                            db.add(track)
                            db.flush()
                        
                        # Créer clé unique pour cette entrée
                        entry_key = (track.id, timestamp)
                        
                        # PRIORITÉ 1: Vérifier si déjà importé en base avec track_id + timestamp
                        # C'est la clé unique de déduplication (même track au même moment = doublon)
                        existing = db.query(ListeningHistory).filter_by(
                            track_id=track.id,
                            timestamp=timestamp
                        ).first()
                        if existing:
                            logger.debug(f"⏭️ Track déjà importé (BD): {track_title} @ {timestamp}")
                            skipped_count += 1
                            continue
                        
                        # PRIORITÉ 2: RÈGLE DES 10 MINUTES DANS LA BASE - TOUJOURS APPLIQUÉE
                        # Éviter les imports dupliqués par Last.fm
                        # Si le même track a été enregistré dans la BD il y a moins de 10 minutes, c'est un doublon
                        recent_same_track = db.query(ListeningHistory).filter(
                            ListeningHistory.track_id == track.id,
                            ListeningHistory.timestamp >= timestamp - 600,  # 10 minutes avant
                            ListeningHistory.timestamp <= timestamp + 600   # 10 minutes après
                        ).first()
                        if recent_same_track:
                            logger.debug(f"⏭️ Règle 10 min (BD): {track_title} trouvé à {recent_same_track.timestamp} (diff: {abs(timestamp - recent_same_track.timestamp)}s)")
                            skipped_count += 1
                            continue
                        
                        # PRIORITÉ 2: Vérifier si DÉJÀ vu dans cette session (avant commit)
                        if entry_key in seen_entries:
                            logger.debug(f"⏭️ Doublon dans session: {track_title} @ {timestamp}")
                            skipped_count += 1
                            continue
                        
                        # PRIORITÉ 3: RÈGLE DES 10 MINUTES - Éviter les scrobbles dupliqués par Last.fm
                        # Si le même track a été écouté il y a moins de 10 minutes, c'est probablement un doublon
                        if track.id in last_import_by_track:
                            last_timestamp, last_history = last_import_by_track[track.id]
                            time_diff_seconds = abs(timestamp - last_timestamp)
                            if time_diff_seconds < 600:  # 10 minutes = 600 secondes
                                logger.debug(f"⏭️ Règle 10 min: {track_title} écouté il y a {time_diff_seconds}s (doublon Last.fm)")
                                skipped_count += 1
                                continue
                        
                        # Créer entrée historique
                        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        history = ListeningHistory(
                            track_id=track.id,
                            timestamp=timestamp,
                            date=dt.strftime("%Y-%m-%d %H:%M"),
                            source='lastfm',
                            loved=False
                        )
                        db.add(history)
                        imported_count += 1
                        seen_entries.add(entry_key)
                        
                        # Tracker pour la règle 10 minutes
                        last_import_by_track[track.id] = (timestamp, history)
                        
                        # Marquer album pour enrichissement
                        if album.id not in albums_to_enrich:
                            albums_to_enrich[album.id] = {
                                'artist': artist_name,
                                'title': album_title,
                                'album_id': album.id
                            }
                        
                        # Commit par petits lots pour éviter timeout
                        if imported_count % 50 == 0:
                            db.commit()
                            logger.info(f"💾 {imported_count} tracks importés...")
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur import track {track_data.get('title', 'Unknown')}: {e}")
                        error_count += 1
                        continue
                
                # Commit après chaque batch
                db.commit()
                logger.info(f"✅ Batch {batch_num + 1} terminé: {imported_count} importés, {skipped_count} ignorés")
                
                # Petit délai entre batches pour ne pas saturer Last.fm API
                if batch_num < num_batches - 1:
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                logger.error(f"❌ Erreur batch {batch_num + 1}: {e}")
                db.rollback()
                continue
        
        db.commit()
        
        # Marquer l'import comme terminé
        _lastfm_import_progress["status"] = "completed"
        _lastfm_import_progress["imported"] = imported_count
        _lastfm_import_progress["skipped"] = skipped_count
        _lastfm_import_progress["errors"] = error_count
        
        logger.info(f"📊 Import terminé: {imported_count} tracks importés, {skipped_count} ignorés, {error_count} erreurs")
        logger.info(f"📀 {len(albums_to_enrich)} nouveaux albums à enrichir")
        
        # Queue enrichment des albums en arrière-plan (ne pas bloquer l'endpoint)
        if len(albums_to_enrich) > 0:
            try:
                from app.services.scheduler_service import SchedulerService
                import asyncio
                from concurrent.futures import ThreadPoolExecutor
                
                scheduler = SchedulerService(settings.dict())
                
                # Créer une fonction wrapper synchrone qui exécute le coroutine
                def run_enrichment():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(scheduler.enrich_imported_albums(albums_to_enrich))
                    finally:
                        loop.close()
                
                # Utiliser ThreadPoolExecutor pour exécuter en arrière-plan sans bloquer
                executor = ThreadPoolExecutor(max_workers=1)
                executor.submit(run_enrichment)
                logger.info(f"✅ Tâche d'enrichissement en arrière-plan démarrée pour {len(albums_to_enrich)} albums")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de démarrer enrichissement en arrière-plan: {e}")
                # Si l'enrichissement en arrière-plan échoue, ce n'est pas critique
                # Les albums resteront dans la DB, juste sans enrichissement
        
        return {
            "status": "success",
            "tracks_imported": imported_count,
            "tracks_skipped": skipped_count,
            "tracks_errors": error_count,
            "albums_to_enrich": len(albums_to_enrich),
            "total_scrobbles": total_scrobbles,
            "note": "Album enrichment (Spotify + IA descriptions) running in background"
        }
        
    except Exception as e:
        _lastfm_import_progress["status"] = "error"
        logger.error(f"❌ Erreur import historique Last.fm: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur import: {str(e)}")

