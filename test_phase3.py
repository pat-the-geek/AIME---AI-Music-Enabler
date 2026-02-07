#!/usr/bin/env python3
"""Test Phase 3 - API reorganization."""
import sys
sys.path.insert(0, 'backend')

try:
    # Test imports from app.api.v1
    from app.api.v1 import (
        collection, artists, collections,
        history,
        playlists, roon,
        services,
        analytics,
        magazines,
        search
    )
    print("✅ All domain imports successful")
    
    # Verify routers exist
    assert hasattr(collection, 'router'), "collection.router missing"
    assert hasattr(artists, 'router'), "artists.router missing"
    assert hasattr(collections, 'router'), "collections.router missing"
    assert hasattr(history, 'router'), "history.router missing"
    assert hasattr(playlists, 'router'), "playlists.router missing"
    assert hasattr(roon, 'router'), "roon.router missing"
    assert hasattr(services, 'router'), "services.router missing"
    assert hasattr(analytics, 'router'), "analytics.router missing"
    assert hasattr(magazines, 'router'), "magazines.router missing"
    assert hasattr(search, 'router'), "search.router missing"
    print("✅ All routers accessible")
    
    # Test main.py import
    from app.main import app
    print("✅ main.py imported successfully")
    
    # Verify routes are registered
    route_count = len(app.routes)
    print(f"✅ Total routes registered: {route_count}")
    
    print("\n✅ Phase 3: API reorganization successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
