#!/usr/bin/env python3
"""Analyse les URLs Spotify dans la base de données."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models.album import Album

db = SessionLocal()

total = db.query(Album).count()
null_urls = db.query(Album).filter(Album.spotify_url == None).count()
empty_urls = db.query(Album).filter(Album.spotify_url == '').count()
with_url = total - null_urls - empty_urls

print('\n' + '='*80)
print('📊 ANALYSE DES URLs SPOTIFY')
print('='*80)
print(f'\nTotal albums: {total}')
print(f'\n🔗 Statut des URLs:')
print(f'  • Albums avec URL Spotify: {with_url} ({int(with_url/total*100)}%)')
print(f'  • Albums sans URL (NULL): {null_urls}')
print(f'  • Albums sans URL (vide): {empty_urls}')
print(f'\n{"✅" if (null_urls + empty_urls) == 0 else "⚠️"} Couverture: {with_url}/{total}')

# Exemples avec URLs
if with_url > 0:
    print(f'\n📝 Exemples d\'albums AVEC URL Spotify:')
    with_url_ex = db.query(Album).filter(
        Album.spotify_url != None,
        Album.spotify_url != ''
    ).limit(5).all()
    for album in with_url_ex:
        artists = ', '.join([a.name for a in album.artists[:1]])
        print(f'\n  • {album.title[:40]} - {artists[:30]}')
        print(f'    → {album.spotify_url}')

# Exemples sans URLs
if null_urls + empty_urls > 0:
    print(f'\n❌ Exemples d\'albums SANS URL Spotify:')
    no_url_ex = db.query(Album).filter(
        (Album.spotify_url == None) | (Album.spotify_url == '')
    ).limit(5).all()
    for album in no_url_ex:
        artists = ', '.join([a.name for a in album.artists[:1]])
        print(f'  • {album.title[:40]} - {artists[:30]}')

print('\n' + '='*80)
print('\n💡 Note: Les albums sans URL Spotify peuvent être enrichis via')
print('   l\'endpoint POST /api/v1/tracking/services/spotify/enrich-all')
print('='*80 + '\n')

db.close()
