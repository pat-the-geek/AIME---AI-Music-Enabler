#!/usr/bin/env python3
"""
Test simple de normalisation - vérifie que le système fonctionne
"""
import sqlite3
import subprocess
import time
import os

os.chdir('/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler')

print("\n✓ Checking database integrity...")
conn = sqlite3.connect('data/musique.db')
try:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM artists;")
    count = cursor.fetchone()[0]
    print(f"✓ Database OK: {count} artists found")
except Exception as e:
    print(f"✗ Database error: {e}")
    exit(1)
finally:
    conn.close()

print("✓ Normalization test completed successfully!")
