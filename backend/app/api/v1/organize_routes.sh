#!/bin/bash
# Script to organize routes by domain

# Create remaining directories
mkdir -p analytics
mkdir -p magazines
mkdir -p search

# Move collection routes
mv collection.py collection/albums.py
mv collections.py collection/album_collections.py
mv artists.py collection/artists.py

# Move content routes
mv history.py content/history.py

# Move playback routes
mv playlists.py playback/playlists.py
mv roon.py playback/roon.py

# Move tracking routes
mv services.py tracking/services.py

# Move other routes
mv analytics.py analytics/analytics.py
mv magazines.py magazines/magazines.py
mv search.py search/search.py

echo "✅ Routes organized by domain"
ls -la */
