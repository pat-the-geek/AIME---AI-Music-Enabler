#!/usr/bin/env python3
"""Rafraîchissement COMPLET de tous les albums de la collection."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album
from backend.app.services.roon_normalization_service import RoonNormalizationService
from backend.app.core.config import get_settings
import time
import logging
from datetime import datetime

# Activer les logs détaillés
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)

print("\n" + "=" * 80)
print("🔄 RAFRAÎCHISSEMENT COMPLET - TOUS LES ALBUMS")
print("=" * 80)

try:
    # Récupérer la configuration
    settings = get_settings()
    bridge_url = settings.app_config.get('roon_bridge_url', 'http://localhost:3330')
    
    # Créer le service de normalisation
    norm_service = RoonNormalizationService(bridge_url=bridge_url)
    
    # Vérifier la connexion à Roon
    print("\n🔌 Vérification connexion Roon...")
    if not norm_service.is_connected():
        print("❌ Bridge Roon non connecté!")
        print("   Assurez-vous que Roon est en cours d'exécution et le bridge démarré.")
        sys.exit(1)
    
    print("✅ Bridge Roon connecté\n")
    
    # Récupérer la liste de tous les albums
    db = SessionLocal()
    total_albums = db.query(Album).count()
    print(f"📊 Total albums en collection: {total_albums}\n")
    
    if total_albums == 0:
        print("❌ Aucun album trouvé en collection!")
        db.close()
        sys.exit(1)
    
    # Lancer la normalisation
    print("⚙️ Normalisation des albums avec Roon...\n")
    start_time = time.time()
    
    try:
        stats = norm_service.normalize_with_roon(db)
        elapsed = time.time() - start_time
        
        # Résultats
        print(f"\n✅ Rafraîchissement complété")
        print("=" * 80)
        print(f"📊 Résumé normalisation:")
        print(f"  Artistes normalisés: {stats.get('artists_updated', 0)}")
        print(f"  Albums normalisés: {stats.get('albums_updated', 0)}/{total_albums}")
        print(f"  Tracks trouvées: {stats.get('tracks_matched', 0)}")
        print(f"  Temps: {elapsed:.1f}s")
        print(f"  Taux: {stats.get('albums_updated', 0) / max(elapsed, 1):.1f} albums/s")
        
        # Calcul du taux de réussite
        success_rate = (stats.get('albums_updated', 0) / total_albums * 100) if total_albums > 0 else 0
        print(f"\n📈 Taux de succès: {success_rate:.1f}% ({stats.get('albums_updated', 0)}/{total_albums})")
        
        if success_rate > 90:
            print(f"✅ Excellemment rafraîchi!")
        elif success_rate > 70:
            print(f"⚠️ Partiellement rafraîchi (certains albums non trouvés dans Roon)")
        else:
            print(f"⚠️ Peu de succès (vérifiez que les albums sont dans Roon)")
        
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"❌ Erreur normalisation: {e}")
        db.rollback()
        print("=" * 80 + "\n")
        raise
    finally:
        db.close()

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 80 + "\n")
    sys.exit(1)
