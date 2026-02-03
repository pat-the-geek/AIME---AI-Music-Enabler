#!/usr/bin/env python3
"""
Diagnostic complet - Vérifier l'état des métadonnées IA par source.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import text
from app.database import SessionLocal

def check_ai_metadata_status():
    """Analyser le statut des métadonnées IA par source."""
    db = SessionLocal()
    
    try:
        print("\n" + "="*80)
        print("📊 DIAGNOSTIC - ÉTAT DES MÉTADONNÉES IA PAR SOURCE")
        print("="*80 + "\n")
        
        # 1. Compter les albums par source
        print("1️⃣ ALBUMS PAR SOURCE:")
        print("-" * 80)
        
        query_result = db.execute(text("""
        SELECT 
            al.source,
            COUNT(DISTINCT al.id) as total_albums,
            COUNT(DISTINCT CASE WHEN m.id IS NOT NULL THEN al.id END) as with_ai,
            COUNT(DISTINCT CASE WHEN m.id IS NULL THEN al.id END) as without_ai,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN m.id IS NOT NULL THEN al.id END) / 
                  COUNT(DISTINCT al.id), 1) as ai_coverage_percent
        FROM albums al
        LEFT JOIN metadata m ON al.id = m.album_id
        GROUP BY al.source
        ORDER BY total_albums DESC
        """))
        
        for row in query_result:
            source, total, with_ai, without_ai, coverage = row
            print(f"  {source:12} : {total:4} albums | {with_ai:4} avec IA | {without_ai:4} sans IA | {coverage:5.1f}% couverture")
        
        # 2. Albums récents sans IA par source
        print("\n2️⃣ ALBUMS RÉCENTS SANS IA (dernières 24h):")
        print("-" * 80)
        
        query_result = db.execute(text("""
        SELECT 
            al.id,
            al.title,
            al.source,
            COUNT(lh.id) as play_count,
            MIN(lh.date) as first_play,
            MAX(lh.date) as last_play
        FROM albums al
        LEFT JOIN tracks tr ON al.id = tr.album_id
        LEFT JOIN listening_history lh ON tr.id = lh.track_id
        LEFT JOIN metadata m ON al.id = m.album_id
        WHERE m.id IS NULL
        AND al.id >= 1410
        GROUP BY al.id
        ORDER BY al.id DESC
        """))
        
        rows = query_result.fetchall()
        if rows:
            for album_id, title, source, play_count, first_play, last_play in rows:
                status_icon = "⚠️" if source != "manual" else "ℹ️"
                print(f"  {status_icon} ID {album_id:4} | {source:8} | {title:50} | {play_count} plays")
        else:
            print("  ✅ Aucun album sans IA (tous ont des métadonnées!)")
        
        # 3. Comparaison Last.fm vs Roon
        print("\n3️⃣ COMPARAISON LAST.FM vs ROON:")
        print("-" * 80)
        
        query_result = db.execute(text("""
        SELECT 
            'lastfm' as source,
            COUNT(DISTINCT al.id) as total,
            COUNT(DISTINCT CASE WHEN m.id IS NOT NULL THEN al.id END) as with_ai,
            COUNT(DISTINCT CASE WHEN m.id IS NULL THEN al.id END) as without_ai
        FROM albums al
        LEFT JOIN metadata m ON al.id = m.album_id
        WHERE al.source = 'lastfm'
        
        UNION ALL
        
        SELECT 
            'roon' as source,
            COUNT(DISTINCT al.id) as total,
            COUNT(DISTINCT CASE WHEN m.id IS NOT NULL THEN al.id END) as with_ai,
            COUNT(DISTINCT CASE WHEN m.id IS NULL THEN al.id END) as without_ai
        FROM albums al
        LEFT JOIN metadata m ON al.id = m.album_id
        WHERE al.source = 'roon'
        """))
        
        lastfm_data = None
        roon_data = None
        
        for row in query_result:
            source, total, with_ai, without_ai = row
            if source == 'lastfm':
                lastfm_data = (total, with_ai, without_ai)
            else:
                roon_data = (total, with_ai, without_ai)
        
        if lastfm_data:
            total, with_ai, without_ai = lastfm_data
            coverage = (with_ai * 100.0 / total) if total > 0 else 0
            print(f"  Last.fm: {total:4} albums | {with_ai:4} avec IA | {without_ai:4} sans IA | {coverage:5.1f}%")
        
        if roon_data:
            total, with_ai, without_ai = roon_data
            coverage = (with_ai * 100.0 / total) if total > 0 else 0
            print(f"  Roon   : {total:4} albums | {with_ai:4} avec IA | {without_ai:4} sans IA | {coverage:5.1f}%")
            
            if without_ai > 0:
                print(f"\n  ⚠️  ROON: {without_ai} albums sans IA - CORRECTION APPLIQUÉE!")
        
        # 4. Résumé global
        print("\n4️⃣ RÉSUMÉ GLOBAL:")
        print("-" * 80)
        
        query_result = db.execute(text("""
        SELECT 
            COUNT(DISTINCT al.id) as total_albums,
            COUNT(DISTINCT CASE WHEN m.id IS NOT NULL THEN al.id END) as with_ai,
            COUNT(DISTINCT CASE WHEN m.id IS NULL AND al.source != 'manual' THEN al.id END) as without_ai_auto,
            COUNT(DISTINCT CASE WHEN m.id IS NULL AND al.source = 'manual' THEN al.id END) as without_ai_manual
        FROM albums al
        LEFT JOIN metadata m ON al.id = m.album_id
        """))
        
        total_albums, with_ai, without_ai_auto, without_ai_manual = query_result.fetchone()
        
        print(f"  Total albums:          {total_albums}")
        print(f"  ✅ Avec IA:             {with_ai}")
        print(f"  ⚠️  Sans IA (auto):      {without_ai_auto} ← À enrichir")
        print(f"  ℹ️  Sans IA (manual):    {without_ai_manual} (normal)")
        
        coverage = (with_ai * 100.0 / total_albums) if total_albums > 0 else 0
        print(f"\n  📊 COUVERTURE IA GLOBALE: {coverage:.1f}%")
        
        if without_ai_auto > 0:
            print(f"\n  💡 Pour enrichir les {without_ai_auto} albums manquants:")
            print("     python3 enrich_missing_ai.py")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_ai_metadata_status()
