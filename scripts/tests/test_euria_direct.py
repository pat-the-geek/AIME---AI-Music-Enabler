#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[2]
env_path = project_root / 'config' / '.env'
fallback_env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
elif fallback_env_path.exists():
    load_dotenv(fallback_env_path)

# Test Euria API
EURIA_URL = os.getenv('URL', 'https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions')
EURIA_BEARER = os.getenv('bearer', '')

print(f"URL: {EURIA_URL}")
print(f"Bearer token: {EURIA_BEARER[:20]}..." if EURIA_BEARER else "❌ NO TOKEN")

if EURIA_BEARER:
    try:
        payload = {
            "model": "mistral-large",
            "messages": [{
                "role": "user",
                "content": "Test: Generate a short music review for an album."
            }],
            "max_tokens": 100
        }
        
        print(f"\n📤 Envoi test à Euria...")
        response = requests.post(
            EURIA_URL,
            json=payload,
            headers={"Authorization": f"Bearer {EURIA_BEARER}"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data:
                content = data['choices'][0].get('message', {}).get('content', '')
                print(f"✅ Response: {content[:150]}...")
            else:
                print(f"❌ Format incorrect: {list(data.keys())}")
        else:
            print(f"❌ Error status {response.status_code}: {response.text[:300]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
else:
    print("❌ No bearer token!")
