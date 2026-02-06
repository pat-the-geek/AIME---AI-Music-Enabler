#!/usr/bin/env python3
"""
Test de simulation simple - vérifier avec logs détaillés
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

print("\n" + "="*60)
print("TEST 1: Première simulation")
print("="*60)

# Lancer test 1
r = requests.post(f"{BASE_URL}/services/roon/normalize/simulate", params={"limit": 10})
print(f"1️⃣  POST response: {r.status_code}")
data = r.json()
print(f"   Status endpoint ready: {data.get('status_endpoint')}")

# Poll pour complétion test 1
for i in range(15):
    r = requests.get(f"{BASE_URL}/services/roon/normalize/simulate-results")
    status = r.json().get("status")
    print(f"   Poll {i+1}: {status}")
    if status == "completed":
        print(f"✅ Test 1 COMPLET")
        break
    time.sleep(0.5)

print("\n⏸️  Pause 2 secondes...")
time.sleep(2)

print("\n" + "="*60)
print("TEST 2: Deuxième simulation")
print("="*60)

# Lancer test 2
r = requests.post(f"{BASE_URL}/services/roon/normalize/simulate", params={"limit": 10})
print(f"2️⃣  POST response: {r.status_code}")
data = r.json()
print(f"   Status endpoint ready: {data.get('status_endpoint')}")

# Poll pour complétion test 2
for i in range(15):
    r = requests.get(f"{BASE_URL}/services/roon/normalize/simulate-results")
    result_data = r.json()
    status = result_data.get("status")
    print(f"   Poll {i+1}: status={status}")
    
    # Afficher les détails si erreur
    if status == "error":
        print(f"   ❌ ERREUR: {result_data.get('error')}")
        break
    
    if status == "completed":
        print(f"✅ Test 2 COMPLET")
        break
    
    time.sleep(0.5)

if status not in ("completed", "error"):
    print(f"❌ TIMEOUT - Test 2 ne s'est pas complété")
    print(f"   État final: {result_data}")

print("\n" + "="*60)
