#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

EURIA_URL = os.getenv('URL', '').replace('/chat/completions', '/models')
EURIA_BEARER = os.getenv('bearer', '')

print(f"Checking models at: {EURIA_URL}")

if EURIA_BEARER and EURIA_URL:
    try:
        response = requests.get(
            EURIA_URL,
            headers={"Authorization": f"Bearer {EURIA_BEARER}"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print("✅ Available models:")
                for model in data['data']:
                    print(f"  - {model.get('id', model)}")
            else:
                print(f"Response: {data}")
        else:
            print(f"Error: {response.text[:500]}")
    except Exception as e:
        print(f"Exception: {e}")

# Also try direct model list endpoint
print("\n" + "="*60)
print("Trying alternative endpoints...")

EURIA_BASE = os.getenv('URL', '').rsplit('/', 2)[0] if '/' in os.getenv('URL', '') else ''
print(f"Base URL: {EURIA_BASE}\n")

test_models = [
    "mistral",
    "mistral-small", 
    "mistral-medium",
    "gpt-4",
    "gpt-4o",
    "claude-3-sonnet"
]

# Test with each model
for model_name in test_models:
    try:
        response = requests.post(
            os.getenv('URL'),
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            },
            headers={"Authorization": f"Bearer {EURIA_BEARER}"},
            timeout=5
        )
        status = response.status_code
        if status == 200:
            print(f"✅ {model_name}: OK")
        elif status == 400:
            if "invalid" in response.text.lower():
                print(f"❌ {model_name}: Invalid model")
            else:
                print(f"⚠️  {model_name}: 400 (other reason)")
        else:
            print(f"⚠️  {model_name}: {status}")
    except Exception as e:
        print(f"❌ {model_name}: {str(e)[:50]}")
