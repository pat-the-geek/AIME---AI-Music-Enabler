#!/usr/bin/env python3
"""
Database Index Optimization Analyzer and Verification Tool

Use this script to:
1. List all existing indexes
2. Check if optimization indexes are applied
3. Measure query performance before/after
4. Run ANALYZE and VACUUM
"""
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta
import json

DATABASE_PATH = Path(__file__).parent.parent / "data" / "musique.db"
EXPECTED_INDEXES = {
    'tracks': [
        'idx_tracks_album_id',
        'idx_tracks_album_title',
        'idx_tracks_spotify_id',
    ],
    'listening_history': [
        'idx_history_timestamp',
        'idx_history_source',
        'idx_history_date',
        'idx_history_track_timestamp',
        'idx_history_timestamp_source',
        'idx_history_date_source',
    ],
    'albums': [
        'idx_albums_discogs_id',
        'idx_albums_spotify_url',
        'idx_albums_discogs_url',
        'idx_albums_source_created',
        'idx_albums_title_source',
        'idx_albums_year',
    ],
    'images': [
        'idx_image_artist',
        'idx_image_album',
        'idx_images_artist_type',
        'idx_images_album_type',
        'idx_images_source',
    ],
    'metadata': [
        'idx_metadata_album',
        'idx_metadata_film',
        'idx_metadata_film_year',
    ],
    'album_artist': [
        'idx_album_artist_album_id',
        'idx_album_artist_artist_id',
    ],
}


def get_connection():
    """Get database connection."""
    if not DATABASE_PATH.exists():
        print(f"❌ Database not found: {DATABASE_PATH}")
        exit(1)
    return sqlite3.connect(str(DATABASE_PATH))


def list_all_indexes():
    """List all indexes in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, tbl_name, sql 
        FROM sqlite_master 
        WHERE type='index' 
        ORDER BY tbl_name, name
    """)
    
    indexes = {}
    for name, table, sql in cursor.fetchall():
        if table not in indexes:
            indexes[table] = []
        indexes[table].append({
            'name': name,
            'sql': sql if sql else '(auto-created)'
        })
    
    conn.close()
    return indexes


def check_optimization():
    """Check if optimization indexes are applied."""
    all_indexes = list_all_indexes()
    
    print("\n" + "="*70)
    print("📊 DATABASE INDEX OPTIMIZATION CHECK")
    print("="*70)
    
    total_expected = sum(len(indexes) for indexes in EXPECTED_INDEXES.values())
    total_found = 0
    
    for table, expected_idx_names in EXPECTED_INDEXES.items():
        print(f"\n📋 Table: {table.upper()}")
        print("-" * 70)
        
        existing_indexes = all_indexes.get(table, [])
        existing_names = {idx['name'] for idx in existing_indexes}
        
        for expected_idx in expected_idx_names:
            if expected_idx in existing_names:
                print(f"  ✅ {expected_idx}")
                total_found += 1
            else:
                print(f"  ❌ {expected_idx} (MISSING)")
    
    print("\n" + "="*70)
    print(f"📈 SUMMARY: {total_found}/{total_expected} indexes found")
    print("="*70)
    
    if total_found == total_expected:
        print("✅ All optimization indexes are applied!")
    else:
        missing = total_expected - total_found
        print(f"⚠️  {missing} indexes are missing!")
        print("   Run: alembic upgrade 005_optimize_indexes")
    
    return total_found == total_expected


def get_table_stats():
    """Get table row counts and size."""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("📊 TABLE STATISTICS")
    print("="*70)
    
    tables = ['artists', 'albums', 'tracks', 'listening_history', 'images', 'metadata']
    
    total_rows = 0
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_rows += count
        print(f"  {table:20s}: {count:8,d} rows")
    
    print("-" * 70)
    print(f"  {'TOTAL':20s}: {total_rows:8,d} rows")
    
    conn.close()


def benchmark_query(description, query, iterations=3):
    """Benchmark a query and return average time in ms."""
    conn = get_connection()
    cursor = conn.cursor()
    
    times = []
    for _ in range(iterations):
        start = time.time()
        cursor.execute(query)
        cursor.fetchall()  # Force execution
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    conn.close()
    
    return avg_time, times


def run_benchmarks():
    """Run performance benchmark queries."""
    print("\n" + "="*70)
    print("⚡ PERFORMANCE BENCHMARK (3x each)")
    print("="*70)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    history_count = cursor.fetchone()[0]
    conn.close()
    
    if history_count == 0:
        print("❌ No listening history data to benchmark")
        return
    
    benchmarks = [
        (
            "Count by date",
            "SELECT date, COUNT(*) FROM listening_history GROUP BY date"
        ),
        (
            "Count by source",
            "SELECT source, COUNT(*) FROM listening_history GROUP BY source"
        ),
        (
            "Last 7 days",
            """
            SELECT DATE('now', '-7 days') as date_from, 
                   COUNT(*) as count
            FROM listening_history 
            WHERE date >= DATE('now', '-7 days')
            """
        ),
        (
            "Tracks per album",
            """
            SELECT a.title, COUNT(t.id) as track_count
            FROM albums a
            LEFT JOIN tracks t ON a.id = t.album_id
            GROUP BY a.id
            ORDER BY track_count DESC
            LIMIT 20
            """
        ),
        (
            "Albums by source",
            """
            SELECT source, COUNT(*) as count
            FROM albums
            GROUP BY source
            """
        ),
        (
            "Join test: Album + Track + History",
            """
            SELECT a.title, t.title, COUNT(h.id)
            FROM albums a
            JOIN tracks t ON a.id = t.album_id
            LEFT JOIN listening_history h ON t.id = h.track_id
            GROUP BY a.id, t.id
            LIMIT 100
            """
        ),
    ]
    
    print()
    for description, query in benchmarks:
        avg_time, times = benchmark_query(description, query)
        print(f"  {description:35s}: {avg_time:8.2f} ms  {times}")


def analyze_database():
    """Run ANALYZE on the database."""
    print("\n" + "="*70)
    print("🔍 ANALYZING DATABASE")
    print("="*70)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Running ANALYZE... (this may take a moment)")
    cursor.execute("ANALYZE")
    conn.commit()
    conn.close()
    
    print("✅ ANALYZE complete - statistics updated")


def vacuum_database():
    """Run VACUUM on the database to compact and free space."""
    print("\n" + "="*70)
    print("🧹 VACUUMING DATABASE")
    print("="*70)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Running VACUUM... (this may take a moment)")
    cursor.execute("VACUUM")
    conn.commit()
    conn.close()
    
    print("✅ VACUUM complete - database compacted")


def show_index_details():
    """Show detailed information about each index."""
    all_indexes = list_all_indexes()
    
    print("\n" + "="*70)
    print("📚 DETAILED INDEX INFORMATION")
    print("="*70)
    
    for table, indexes in all_indexes.items():
        if not indexes:
            continue
        
        print(f"\n{table.upper()}")
        print("-" * 70)
        
        for idx in indexes:
            print(f"  Index: {idx['name']}")
            if idx['sql']:
                print(f"  SQL:   {idx['sql']}")
            else:
                print(f"  Type:  PRIMARY KEY or AUTOINCREMENT")
            print()


def main():
    """Main function."""
    print("\n🗄️  AIME - Database Optimization Tool v1.0")
    print(f"Database: {DATABASE_PATH}")
    print(f"Updated: {datetime.fromtimestamp(DATABASE_PATH.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check optimization
    is_optimized = check_optimization()
    
    # Show statistics
    get_table_stats()
    
    # Run benchmarks if data exists
    run_benchmarks()
    
    # Show index details
    show_index_details()
    
    # Summary
    print("\n" + "="*70)
    print("📋 RECOMMENDATIONS")
    print("="*70)
    
    if not is_optimized:
        print("""
❌ MISSING OPTIMIZATION:
   
   Run these commands to apply optimization:
   
   cd backend
   alembic upgrade 005_optimize_indexes
   
   Then restart the backend to benefit from performance improvements.
        """)
    else:
        print("""
✅ DATABASE IS OPTIMIZED!

   To improve query performance even further:
   
   1. Run ANALYZE to update statistics
   2. Monitor slow queries in logs  
   3. Add custom indexes if needed
   
   Run this script with '--analyze' to update statistics:
   python verify_indexes.py --analyze
        """)
    
    print("="*70)


if __name__ == "__main__":
    import sys
    
    if "--analyze" in sys.argv:
        analyze_database()
    
    if "--vacuum" in sys.argv:
        vacuum_database()
    
    main()
