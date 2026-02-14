#!/usr/bin/env python3
"""Analyse les URLs Apple Music dans la base de données."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models.album import Album

db = SessionLocal()

total = db.query(Album).count()
null_urls = db.query(Album).filter(Album.apple_music_url == None).count()
empty_urls = db.query(Album).filter(Album.apple_music_url == '').count()
search_urls = db.query(Album).filter(Album.apple_music_url.like('%search?term=%')).count()
direct_urls = total - null_urls - empty_urls - search_urls

print('\n' + '='*80)
print('📊 ANALYSE DÉTAILLÉE DES URLs APPLE MUSIC')
print('='*80)
print(f'\nTotal albums: {total}')
print(f'\n🔗 Types d\'URLs:')
print(f'  • URLs directes (album/id): {direct_urls} ({int(direct_urls/total*100)}%)')
print(f'  • URLs de recherche (search): {search_urls} ({int(search_urls/total*100)}%)')
print(f'  • URLs NULL: {null_urls}')
print(f'  • URLs vides (""): {empty_urls}')
print(f'\n{"✅" if (null_urls + empty_urls) == 0 else "⚠️"} Total avec URL valide: {direct_urls + search_urls}/{total}')

# Exemples URLs directes
print(f'\n📝 Exemples d\'URLs DIRECTES (vraies URLs Apple Music):')
direct_ex = db.query(Album).filter(
    Album.apple_music_url != None,
    Album.apple_music_url != '',
    ~Album.apple_music_url.like('%search?term=%')
).limit(5).all()
for album in direct_ex:
    artists = ', '.join([a.name for a in album.artists[:1]])
    print(f'\n  • {album.title[:40]} - {artists[:30]}')
    print(f'    → {album.apple_music_url}')

# Exemples URLs recherche
print(f'\n🔍 Exemples d\'URLs DE RECHERCHE (fallback):')
search_ex = db.query(Album).filter(Album.apple_music_url.like('%search?term=%')).limit(5).all()
for album in search_ex:
    artists = ', '.join([a.name for a in album.artists[:1]])
    print(f'\n  • {album.title[:40]} - {artists[:30]}')
    print(f'    → {album.apple_music_url[:75]}...')

print('\n' + '='*80)
print('\n💡 Note: Les URLs de recherche sont des fallbacks. Le bouton Apple Music')
print('   devrait être visible pour TOUTES les URLs (directes ET recherche).')
print('='*80 + '\n')

db.close()
