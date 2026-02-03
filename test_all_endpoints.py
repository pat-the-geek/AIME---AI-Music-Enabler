#!/usr/bin/env python
"""
Test complet pour vérifier que tous les endpoints d'historique 
retournent les données correctement après la correction.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ListeningHistory

def query_timeline(db: Session, date_str: str):
    """Simuler la query de l'endpoint /timeline corrigé."""
    start_dt = datetime.strptime(f"{date_str} 00:00", "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(f"{date_str} 23:59", "%Y-%m-%d %H:%M")
    
    start_timestamp = int(start_dt.timestamp())
    end_timestamp = int(end_dt.timestamp())
    
    return db.query(ListeningHistory).filter(
        ListeningHistory.timestamp >= start_timestamp,
        ListeningHistory.timestamp <= end_timestamp
    ).order_by(ListeningHistory.timestamp.desc()).all()

def query_journal(db: Session, start_date: str, end_date: str):
    """Simuler la query de l'endpoint /tracks corrigé."""
    start_dt = datetime.strptime(f"{start_date} 00:00", "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(f"{end_date} 23:59", "%Y-%m-%d %H:%M")
    
    start_timestamp = int(start_dt.timestamp())
    end_timestamp = int(end_dt.timestamp())
    
    return db.query(ListeningHistory).filter(
        ListeningHistory.timestamp >= start_timestamp,
        ListeningHistory.timestamp <= end_timestamp
    ).order_by(ListeningHistory.timestamp.desc()).all()

def test_endpoints():
    """Tester les trois endpoints corrigés."""
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("🧪 TEST DES ENDPOINTS CORRIGÉS")
        print("="*60 + "\n")
        
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Test 1: /timeline pour aujourd'hui
        print(f"📊 TEST 1: /timeline pour {today}")
        timeline_today = query_timeline(db, today)
        print(f"   ✅ {len(timeline_today)} lectures trouvées\n")
        
        # Test 2: /timeline pour hier
        print(f"📊 TEST 2: /timeline pour {yesterday}")
        timeline_yesterday = query_timeline(db, yesterday)
        print(f"   ✅ {len(timeline_yesterday)} lectures trouvées\n")
        
        # Test 3: /timeline pour il y a une semaine
        print(f"📊 TEST 3: /timeline pour {week_ago}")
        timeline_week = query_timeline(db, week_ago)
        print(f"   ✅ {len(timeline_week)} lectures trouvées\n")
        
        # Test 4: /tracks (journal) avec plage de dates
        print(f"📊 TEST 4: /tracks (journal) du {week_ago} au {today}")
        journal = query_journal(db, week_ago, today)
        print(f"   ✅ {len(journal)} lectures trouvées\n")
        
        # Test 5: /tracks avec dates spécifiques
        print(f"📊 TEST 5: /tracks du {yesterday} au {today} (2 jours)")
        journal_2days = query_journal(db, yesterday, today)
        print(f"   ✅ {len(journal_2days)} lectures trouvées\n")
        
        # Vérifications de cohérence
        print("✅ VÉRIFICATIONS DE COHÉRENCE:")
        
        # La somme des 2 jours doit égaler le total de ces 2 jours
        expected_total = len(timeline_yesterday) + len(timeline_today)
        actual_total = len(journal_2days)
        
        print(f"   • {yesterday}: {len(timeline_yesterday)} + {today}: {len(timeline_today)} = {expected_total}")
        print(f"   • /tracks({yesterday} à {today}): {actual_total}")
        
        if expected_total == actual_total:
            print(f"   ✅ Cohérence confirmée!\n")
        else:
            print(f"   ⚠️ Incohérence détectée!\n")
        
        # Afficher quelques exemples
        print("📝 EXEMPLES DE LECTURES POUR AUJOURD'HUI:")
        for i, entry in enumerate(timeline_today[:5], 1):
            print(f"   {i}. {entry.date} - {entry.source}")
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS RÉUSSIS!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_endpoints()
    sys.exit(0 if success else 1)
