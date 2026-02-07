#!/bin/bash
# Commit Phase 2D
cd /Users/patrickostertag/Documents/DataForIA/AIME\ -\ AI\ Music\ Enabler

git add -A

git commit -m "feat: Phase 2D - Consolidate Playback services (playlists + Roon)

- Created PlaylistService: 570+ lines
  - Consolidated: playlist_service + playlist_generator
  - CRUD operations, track management, export, 7 algorithms
  
- Created RoonPlaybackService: 200+ lines
  - Roon playback operations
  
- Fixed playlist models (Playlist, PlaylistTrack)
- Refactored playlists.py: 411 -> 218 lines (-47%)
- All imports verified"

git log -1 --oneline
