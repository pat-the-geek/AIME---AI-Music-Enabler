#!/usr/bin/env python3
"""
Script pour enrichir les albums récents sans métadonnées IA.
Utile pour regénérer les descriptions IA manquantes.
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Album, Metadata, Artist
from app.services.ai_service import AIService
from app.core.config import get_settings
import logging

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def enrich_missing_ai_info():
    """Générer les descriptions IA manquantes pour les albums récents."""
    db = SessionLocal()
    
    try:
        settings = get_settings()
        secrets = settings.secrets
        euria_config = secrets.get('euria', {})
        
        ai_service = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer'),
            max_attempts=euria_config.get('max_attempts', 5),
            default_error_message=euria_config.get('default_error_message', 'Aucune information disponible')
        )
        
        print("\n" + "="*70)
        print("🤖 ENRICHISSEMENT DES DESCRIPTIONS IA MANQUANTES")
        print("="*70 + "\n")
        
        # Trouver les albums sans metadata créés dans les 24 dernières heures
        # (albums à forte probabilité d'être des détections récentes)
        recently_played_limit = datetime.now() - timedelta(hours=24)
        
        # Requête: Albums sans metadata IA
        albums_without_ai = db.query(Album).outerjoin(Metadata).filter(
            Metadata.id == None,  # Albums sans métadonnées
            Album.id >= 1410  # Albums récents (ajustez selon vos IDs)
        ).all()
        
        print(f"📊 {len(albums_without_ai)} albums trouvés sans métadonnées IA\n")
        
        if not albums_without_ai:
            print("✅ Tous les albums ont des métadonnées IA!")
            return
        
        enriched_count = 0
        failed_count = 0
        
        for album in albums_without_ai:
            try:
                # Récupérer le nom de l'artiste principal
                if album.artists:
                    artist_name = album.artists[0].name
                else:
                    logger.warning(f"⚠️ Pas d'artiste pour {album.title}, skip")
                    continue
                
                album_title = album.title
                
                print(f"📝 Enrichissement: {artist_name} - {album_title}...", end=" ")
                
                # Générer l'info IA
                ai_info = await ai_service.generate_album_info(artist_name, album_title)
                
                if ai_info:
                    metadata = Metadata(album_id=album.id, ai_info=ai_info)
                    db.add(metadata)
                    db.commit()
                    print("✅")
                    enriched_count += 1
                    logger.info(f"✅ Info IA générée pour {album_title}")
                else:
                    print("⚠️ (Pas de réponse IA)")
                    failed_count += 1
                    logger.warning(f"⚠️ Aucune info IA générée pour {album_title}")
                
            except Exception as e:
                print(f"❌ ({str(e)[:30]})")
                failed_count += 1
                logger.error(f"❌ Erreur pour {album.title}: {e}")
                db.rollback()
        
        print("\n" + "="*70)
        print(f"📊 RÉSULTATS:")
        print(f"   ✅ Enrichis: {enriched_count}")
        print(f"   ❌ Échoués: {failed_count}")
        print(f"   📋 Total: {enriched_count + failed_count}")
        print("="*70 + "\n")
        
        # Vérification finale
        albums_with_ai_now = db.query(Album).join(Metadata).distinct().count()
        print(f"✅ Total albums avec IA: {albums_with_ai_now}\n")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(enrich_missing_ai_info())
