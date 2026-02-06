#!/usr/bin/env python3
"""ÉTAPE 4: Rafraichissement/Normalisation des albums après import."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.services.roon_normalization_service import RoonNormalizationService
from backend.app.core.config import get_settings
import time
from datetime import datetime

print("\n" + "=" * 80)
print("🔄 ÉTAPE 4: RAFRAÎCHISSEMENT ET NORMALISATION")
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
        print("⚠️ Bridge Roon non connecté")
        print("   Comment résoudre:")
        print("   1. Assurez-vous que Roon est en cours d'exécution")
        print("   2. Vérifiez que le bridge est démarré")
        print("   3. Relancez cette étape une fois connecté")
        print("\n✅ Étape 4 ignorée (Roon non disponible)")
        print("=" * 80 + "\n")
        sys.exit(0)
    
    print("✅ Bridge Roon connecté\n")
    
    # Lancer la normalisation
    print("⚙️ Normalisation des albums avec Roon...")
    db = SessionLocal()
    start_time = time.time()
    
    try:
        stats = norm_service.normalize_with_roon(db)
        elapsed = time.time() - start_time
        
        # Résultats
        print(f"\n✅ Étape 4 complétée")
        print("=" * 80)
        print(f"📊 Résumé normalisation:")
        print(f"  Artistes normalisés: {stats.get('artists_updated', 0)}")
        print(f"  Albums normalisés: {stats.get('albums_updated', 0)}")
        print(f"  Tracks trouvées: {stats.get('tracks_matched', 0)}")
        print(f"  Temps: {elapsed:.1f}s")
        
        if stats.get('artists_updated', 0) > 0 or stats.get('albums_updated', 0) > 0:
            print(f"\n✅ Albums rafraîchis avec succès!")
        else:
            print(f"\n⚠️ Aucune normalisation effectuée (albums déjà synchronisés?)")
        
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
    print("=" * 80 + "\n")
    sys.exit(1)
