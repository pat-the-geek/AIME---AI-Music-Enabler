#!/usr/bin/env python3
"""
Script de nettoyage des doublons dans ListeningHistory.
Utilise la règle des 10 minutes: si le même track a été écouté il y a moins de 10 minutes, c'est un doublon.
"""
import sys
import os

# Ajouter le chemin du projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Initialisation du script de nettoyage...", flush=True)

try:
    from app.database import SessionLocal
    from app.models import ListeningHistory
    from sqlalchemy import func
    print("✅ Imports réussis", flush=True)
except Exception as e:
    print(f"❌ Erreur d'importation: {e}")
    sys.exit(1)

def main():
    print("\n=== NETTOYAGE DES DOUBLONS LASTFM ===\n", flush=True)
    
    db = SessionLocal()
    total_initial = 0
    duplicates_found = 0
    duplicates_deleted = 0
    
    try:
        # Compter les entrées initiales
        total_initial = db.query(ListeningHistory).count()
        print(f"📊 Total initial: {total_initial} entrées", flush=True)
        
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
        
        print(f"📀 Tracks avec doublons potentiels: {len(duplicates)}", flush=True)
        
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
                    duplicates_found += 1
        
        if duplicates_deleted > 0:
            print(f"\n🗑️ Suppression de {duplicates_deleted} doublons...", flush=True)
            db.commit()
            print(f"✅ {duplicates_deleted} doublons supprimés", flush=True)
        else:
            print(f"\n✅ Aucun doublon trouvé!", flush=True)
        
        # Compter les entrées finales
        total_final = db.query(ListeningHistory).count()
        print(f"📊 Total final: {total_final} entrées", flush=True)
        print(f"📉 Supprimé: {total_initial - total_final} entrées\n", flush=True)
        
    except Exception as e:
        print(f"❌ Erreur: {e}", flush=True)
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
    print("✅ Script terminé", flush=True)

