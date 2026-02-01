#!/usr/bin/env python3
"""
Test script for Last.fm import enhancement.
Verifies that the endpoint correctly handles:
- limit=None (import ALL)
- limit=1000 (import 1000)
- limit=500 (import 500)
"""

import requests
import json
from typing import Optional

API_BASE_URL = "http://localhost:8000"

def test_import(limit: Optional[int] = None, description: str = "") -> dict:
    """Test the import endpoint with a specific limit."""
    
    # Build URL
    params = {"skip_existing": "true"}
    if limit is not None:
        params["limit"] = limit
    
    url = f"{API_BASE_URL}/services/lastfm/import-history"
    
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Limit: {limit}")
    
    try:
        response = requests.post(url, params=params, timeout=600)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS:")
            print(f"  - Tracks Imported: {data.get('tracks_imported', 0)}")
            print(f"  - Tracks Skipped: {data.get('tracks_skipped', 0)}")
            print(f"  - Tracks Errors: {data.get('tracks_errors', 0)}")
            print(f"  - Albums Enriched: {data.get('albums_enriched', 0)}")
            print(f"  - Total Albums to Enrich: {data.get('total_albums_to_enrich', 0)}")
            print(f"  - Total Scrobbles (user): {data.get('total_scrobbles', 0)}")
            return data
        else:
            print(f"\n❌ ERROR: Status {response.status_code}")
            print(f"Response: {response.text}")
            return {}
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        return {}

def main():
    """Run all tests."""
    
    print("\n" + "="*60)
    print("LAST.FM IMPORT ENHANCEMENT TEST SUITE")
    print("="*60)
    
    # Test 1: Import ALL scrobbles (new default)
    test_import(
        limit=None,
        description="Import ALL scrobbles (limit=None, new default)"
    )
    
    # Test 2: Import 1000 (old default)
    test_import(
        limit=1000,
        description="Import 1000 scrobbles (old default, backward compatibility)"
    )
    
    # Test 3: Import 500 (quick option)
    test_import(
        limit=500,
        description="Import 500 scrobbles (quick option)"
    )
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)
    print("\nExpected Results:")
    print("1. limit=None should import ALL scrobbles (e.g., 2000+)")
    print("2. limit=1000 should import exactly 1000 (or fewer if less available)")
    print("3. limit=500 should import exactly 500 (or fewer if less available)")
    print("\nNote: Run this test ONLY when backend is running!")
    print("Backend must have Last.fm credentials configured.\n")

if __name__ == "__main__":
    main()
