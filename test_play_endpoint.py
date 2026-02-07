#!/usr/bin/env python3
"""Test script to verify the play-album-by-name endpoint works quickly"""
import subprocess
import time
import sys
import httpx

# Kill existing services
subprocess.run(["pkill", "-9", "python3"], capture_output=True)
subprocess.run(["pkill", "-9", "node"], capture_output=True)
time.sleep(2)

# Start bridge
print("🌉 Démarrage du bridge...")
bridge_proc = subprocess.Popen(
    ["node", "roon-bridge/app.js"],
    stdout=open("/tmp/bridge.log", "w"),
    stderr=subprocess.STDOUT,
    cwd="/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
)
time.sleep(3)

# Start backend
print("⚙️  Démarrage du backend...")
backend_proc = subprocess.Popen(
    ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=open("/tmp/backend.log", "w"),
    stderr=subprocess.STDOUT,
    cwd="/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend"
)
time.sleep(5)

# Test endpoint
print("🧪 Test de l'endpoint play-album-by-name...")
try:
    start = time.time()
    response = httpx.post(
        "http://localhost:8000/api/v1/roon/play-album-by-name",
        json={
            "artist_name": "Gold Panda",
            "album_title": "Lucky Shiner (Deluxe Edition)"
        },
        timeout=5.0
    )
    elapsed = time.time() - start
    
    print(f"✓ Réponse reçue en {elapsed:.2f}s")
    print(f"  Status: {response.status_code}")
    print(f"  Body: {response.json()}")
    
    if elapsed < 2.0:
        print("✅ L'endpoint retourne très rapidement (< 2s) - OK!")
    else:
        print(f"⚠️  L'endpoint prend {elapsed:.1f}s - trop lent")
        
except httpx.TimeoutException:
    print("❌ L'endpoint a timeout (5s) - toujours bloquant!")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Cleanup
bridge_proc.terminate()
backend_proc.terminate()
print("\n✓ Test terminé")
