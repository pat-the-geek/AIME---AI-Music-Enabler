#!/usr/bin/env python3
from app.database import SessionLocal
from app.models import Album
from sqlalchemy import func

db = SessionLocal()

# Albums par source
by_source = db.query(Album.source, func.count(Album.id)).group_by(Album.source).all()
print("📊 Albums par source:")
for source, count in by_source:
    print(f"  - {source}: {count}")

# Dates de création des albums discogs
discogs_albums = db.query(Album.created_at, Album.title).filter(Album.source == 'discogs').order_by(Album.created_at.desc()).limit(10).all()
print("\n📅 10 derniers albums Discogs importés:")
for created, title in discogs_albums:
    print(f"  - {created}: {title}")

# Premier et dernier album discogs
first = db.query(Album.created_at, Album.title).filter(Album.source == 'discogs').order_by(Album.created_at).first()
last = db.query(Album.created_at, Album.title).filter(Album.source == 'discogs').order_by(Album.created_at.desc()).first()
print(f"\n📆 Plage d'import Discogs:")
print(f"  Premier: {first[0]} - {first[1]}")
print(f"  Dernier: {last[0]} - {last[1]}")

db.close()
