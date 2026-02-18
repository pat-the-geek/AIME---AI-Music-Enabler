#!/bin/bash
# Relance l'enrichissement des images pour tous les albums sans image
# Usage : bash scripts/enrich_missing_album_images.sh

cd "$(dirname "$0")/.."

while true; do
    MISSING=$(docker-compose exec backend python -c "import sqlite3; conn = sqlite3.connect('/app/data/db/musique.db'); c = conn.cursor(); print(c.execute(\"SELECT COUNT(*) FROM albums WHERE image_url IS NULL OR image_url = ''\").fetchone()[0]); conn.close()")
    echo "Albums sans image : $MISSING"
    if [ "$MISSING" -eq 0 ]; then
        echo "✅ Tous les albums ont une image."
        break
    fi
    docker-compose exec backend python enrich_lastfm_latest_detection.py --force-all
    sleep 10
    # Pour éviter les rate limits API, ajustez le sleep si besoin
    # (par exemple sleep 60)
done
