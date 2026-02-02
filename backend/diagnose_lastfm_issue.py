#!/usr/bin/env python
"""
Script de diagnostic pour résoudre le problème des lectures Last.fm 
non affichées dans la timeline ou le journal.
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import ListeningHistory, Track, Album, Artist, Image
import logging

# Configurer le logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def diagnose():
    """Exécuter le diagnostic complet."""
    print("\n" + "="*70)
    print("🔍 DIAGNOSTIC - Problème Lectures Last.fm dans Timeline/Journal")
    print("="*70)
    
    db = SessionLocal()
    try:
        # 1. Compter les entrées de l'historique
        print("\n1️⃣  ENTRÉES D'HISTORIQUE")
        print("-" * 70)
        total_history = db.query(ListeningHistory).count()
        print(f"   Total entries: {total_history}")
        
        if total_history == 0:
            print("   ⚠️ AUCUNE ENTRÉE! Le tracker n'a enregistré aucune lecture.")
        
        # 2. Vérifier les sources
        print("\n2️⃣  RÉPARTITION PAR SOURCE")
        print("-" * 70)
        lastfm_count = db.query(ListeningHistory).filter_by(source='lastfm').count()
        roon_count = db.query(ListeningHistory).filter_by(source='roon').count()
        print(f"   Last.fm: {lastfm_count}")
        print(f"   Roon:    {roon_count}")
        
        if lastfm_count == 0:
            print("   ⚠️ AUCUNE LECTURE LAST.FM! Cela explique le problème.")
        
        # 3. Vérifier les entrées récentes
        print("\n3️⃣  ENTRÉES RÉCENTES (24 dernières heures)")
        print("-" * 70)
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)
        
        recent = db.query(ListeningHistory).filter(
            ListeningHistory.timestamp >= int(day_ago.timestamp())
        ).order_by(ListeningHistory.timestamp.desc()).all()
        
        print(f"   Total récentes: {len(recent)}")
        
        if recent:
            for entry in recent[:5]:  # Afficher les 5 premières
                track = entry.track
                album = track.album if track else None
                artist = album.artists[0].name if album and album.artists else "Unknown"
                print(f"   - {entry.date} | {artist} - {track.title} ({entry.source})")
        else:
            print("   ⚠️ AUCUNE ENTRÉE RÉCENTE (< 24h)")
        
        # 4. Vérifier les TOUTES les entrées triées par date
        print("\n4️⃣  DERNIÈRES ENTRÉES (tous les temps)")
        print("-" * 70)
        all_entries = db.query(ListeningHistory).order_by(
            ListeningHistory.timestamp.desc()
        ).limit(10).all()
        
        if all_entries:
            for entry in all_entries:
                track = entry.track
                album = track.album if track else None
                artist = album.artists[0].name if album and album.artists else "Unknown"
                print(f"   - {entry.date} | {artist} - {track.title} ({entry.source})")
        else:
            print("   ❌ AUCUNE ENTRÉE TROUVÉE")
        
        # 5. Vérifier un jour spécifique (aujourd'hui)
        print("\n5️⃣  ENTRÉES D'AUJOURD'HUI")
        print("-" * 70)
        today_date = now.strftime("%Y-%m-%d")
        today_start = f"{today_date} 00:00"
        today_end = f"{today_date} 23:59"
        
        print(f"   Recherche: {today_start} à {today_end}")
        
        today_entries = db.query(ListeningHistory).filter(
            ListeningHistory.date >= today_start,
            ListeningHistory.date <= today_end
        ).order_by(ListeningHistory.timestamp.desc()).all()
        
        print(f"   Trouvées: {len(today_entries)}")
        
        if today_entries:
            for entry in today_entries[:5]:
                track = entry.track
                album = track.album if track else None
                artist = album.artists[0].name if album and album.artists else "Unknown"
                print(f"   - {entry.date} | {artist} - {track.title}")
        else:
            print(f"   ⚠️ Aucune entrée pour aujourd'hui ({today_date})")
        
        # 6. Vérifier les problèmes potentiels
        print("\n6️⃣  VÉRIFICATIONS")
        print("-" * 70)
        
        # Vérifier s'il y a des entrées sans track_id
        orphan_entries = db.query(ListeningHistory).filter(
            ListeningHistory.track_id == None
        ).count()
        if orphan_entries > 0:
            print(f"   ⚠️ {orphan_entries} entrées sans track_id!")
        else:
            print("   ✅ Pas d'entrées orphelines")
        
        # Vérifier le format de date
        if all_entries:
            entry = all_entries[0]
            print(f"   ✅ Format de date: '{entry.date}' (attendu: 'YYYY-MM-DD HH:MM')")
        
        # Vérifier les timestamps
        if all_entries:
            entry = all_entries[0]
            ts = entry.timestamp
            dt = datetime.fromtimestamp(ts)
            print(f"   ✅ Timestamp: {ts} -> {dt.isoformat()}")
        
        # 7. Résumé et recommandations
        print("\n7️⃣  RÉSUMÉ & RECOMMANDATIONS")
        print("-" * 70)
        
        if total_history == 0:
            print("   ❌ PROBLÈME: Aucune lecture n'a été enregistrée")
            print("      - Vérifier que le tracker Last.fm est démarré")
            print("      - Vérifier que les API Last.fm sont configurées")
            print("      - Consulter les logs: docker-compose logs backend")
        elif lastfm_count == 0:
            print("   ⚠️ PROBLÈME: Aucune lecture Last.fm enregistrée")
            print("      - Seul Roon enregistre des lectures")
            print("      - Le tracker Last.fm n'est peut-être pas actif")
        else:
            if len(recent) == 0:
                print("   ⚠️ ATTENTION: Dernières lectures datent de plus de 24h")
                print("      - Vérifier que le tracker est en cours d'exécution")
                print("      - Vérifier les logs pour les erreurs")
            else:
                print("   ✅ Les lectures sont enregistrées correctement")
                print("      - Format de date OK")
                print("      - Timeline devrait fonctionner")
        
        print("\n" + "="*70 + "\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    diagnose()
