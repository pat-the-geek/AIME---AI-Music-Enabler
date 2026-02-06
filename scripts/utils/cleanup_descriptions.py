#!/usr/bin/env python3
import sys
import os
os.chdir('/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.database import SessionLocal
from app.models import Album

db = SessionLocal()

# Nettoyer les anciennes descriptions
count = db.query(Album).filter(Album.ai_description.isnot(None)).count()
if count > 0:
    db.query(Album).update({Album.ai_description: None})
    db.commit()
    print(f"✅ {count} descriptions anciens supprimées")
else:
    print(f"ℹ️  Aucune description trouvée à supprimer")

# Count albums to enrich
total = db.query(Album).filter_by(source='discogs').count()
print(f"📊 {total} albums à enrichir")

db.close()
