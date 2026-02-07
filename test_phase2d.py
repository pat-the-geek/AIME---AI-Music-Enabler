#!/usr/bin/env python3
"""Test Phase 2D imports."""
import sys
sys.path.insert(0, 'backend')

try:
    from app.services.playback import PlaylistService, RoonPlaybackService
    print("✅ Playback services imported successfully")
    
    from app.api.v1 import playlists
    print("✅ Playlists router imported successfully")
    
    print("\n✅ Phase 2D: All imports working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
