#!/usr/bin/env python
"""Test pour vérifier que la timeline retourne les données correctement."""

import sys
import os
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ListeningHistory

def test_timeline_today():
    """Vérifier que la timeline retourne les données pour aujourd'hui."""
    db = SessionLocal()
    
    try:
        # Date d'aujourd'hui
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Test: Récupération des lectures pour {today}")
        
        # Convertir en timestamps (comme le ferait le endpoint fixé)
        start_dt = datetime.strptime(f"{today} 00:00", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{today} 23:59", "%Y-%m-%d %H:%M")
        
        start_timestamp = int(start_dt.timestamp())
        end_timestamp = int(end_dt.timestamp())
        
        print(f"⏰ Timestamps: {start_timestamp} à {end_timestamp}")
        
        # Query avec les timestamps corrects
        history = db.query(ListeningHistory).filter(
            ListeningHistory.timestamp >= start_timestamp,
            ListeningHistory.timestamp <= end_timestamp
        ).order_by(ListeningHistory.timestamp.desc()).all()
        
        print(f"✅ Résultat: {len(history)} lectures trouvées pour {today}")
        
        if history:
            for i, entry in enumerate(history[:3], 1):
                dt = datetime.fromtimestamp(entry.timestamp)
                print(f"  {i}. {entry.date} - {entry.track.title if entry.track else '?'}")
        
        assert len(history) > 0, f"❌ Aucune lecture trouvée pour {today}!"
        print("\n✅ TEST RÉUSSI: Timeline retourne les données correctement!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_timeline_today()
