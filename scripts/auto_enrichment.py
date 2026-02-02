#!/usr/bin/env python3
"""Service d'enrichissement automatique des albums"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Album, Image
import httpx
import json
from typing import Optional

class AlbumEnricher:
    """Service pour enrichir les albums avec des données additionnelles"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def enrich_album(self, album: Album) -> dict:
        """Enrichir un album avec tous les moyens disponibles"""
        results = {
            'album_id': album.id,
            'title': album.title,
            'images_added': 0,
            'errors': []
        }
        
        # 1. Ajouter une image si manquante
        if not album.images:
            image_url = self._find_image(album)
            if image_url:
                try:
                    image = Image(
                        album_id=album.id,
                        source='enrichment',
                        url=image_url
                    )
                    self.db.add(image)
                    self.db.commit()
                    results['images_added'] += 1
                except Exception as e:
                    results['errors'].append('Image error: {}'.format(str(e)))
        
        # 2. Ajouter description AI si manquante
        if not album.ai_description:
            description = self._generate_description(album)
            if description:
                try:
                    album.ai_description = description
                    self.db.commit()
                except Exception as e:
                    results['errors'].append('Description error: {}'.format(str(e)))
        
        # 3. Ajouter genre si manquant
        if not album.genre:
            genre = self._detect_genre(album)
            if genre:
                try:
                    album.genre = genre
                    self.db.commit()
                except Exception as e:
                    results['errors'].append('Genre error: {}'.format(str(e)))
        
        return results
    
    def _find_image(self, album: Album) -> Optional[str]:
        """Chercher une image pour l'album"""
        if not album.artists:
            return None
        
        artist_name = album.artists[0].name
        
        # 1. Essayer MusicBrainz
        image_url = self._search_musicbrainz(album.title, artist_name)
        if image_url:
            return image_url
        
        # 2. Essayer Discogs si l'album a un discogs_id
        if album.discogs_id:
            image_url = self._search_discogs(album.discogs_id)
            if image_url:
                return image_url
        
        # 3. Essayer Spotify en dernier recours
        image_url = self._search_spotify(album.title, artist_name)
        if image_url:
            return image_url
        
        return None
    
    def _search_musicbrainz(self, album_title: str, artist_name: str) -> Optional[str]:
        """Chercher sur MusicBrainz"""
        try:
            headers = {'User-Agent': 'AIMusic/1.0'}
            response = httpx.get(
                'https://musicbrainz.org/ws/2/release',
                params={
                    'query': '{} {}'.format(album_title, artist_name),
                    'limit': 1,
                    'fmt': 'json'
                },
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('releases'):
                    release_id = data['releases'][0].get('id')
                    if release_id:
                        # Chercher l'image via Cover Art Archive
                        cover_response = httpx.get(
                            'https://coverartarchive.org/release/{}/front'.format(release_id),
                            timeout=5
                        )
                        if cover_response.status_code == 200:
                            return str(cover_response.url)
        except:
            pass
        
        return None
    
    def _search_discogs(self, discogs_id: str) -> Optional[str]:
        """Chercher sur Discogs"""
        try:
            headers = {'User-Agent': 'AIMusic/1.0'}
            response = httpx.get(
                'https://api.discogs.com/releases/{}'.format(discogs_id),
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                images = data.get('images', [])
                if images:
                    return images[0].get('uri')
        except:
            pass
        
        return None
    
    def _search_spotify(self, album_title: str, artist_name: str) -> Optional[str]:
        """Chercher sur Spotify"""
        try:
            # Cette fonction nécessite une authentification
            # Retourner None pour l'instant
            pass
        except:
            pass
        
        return None
    
    def _generate_description(self, album: Album) -> Optional[str]:
        """Générer une description pour l'album"""
        # Template simple basé sur les métadonnées
        artists = ', '.join([a.name for a in album.artists[:3]])
        
        if album.year:
            description = '{} par {} ({})'.format(album.title, artists, album.year)
        else:
            description = '{} par {}'.format(album.title, artists)
        
        return description if description else None
    
    def _detect_genre(self, album: Album) -> Optional[str]:
        """Détecter le genre basé sur les titres des pistes"""
        if not album.tracks:
            return None
        
        # Mots-clés pour détecter les genres
        genre_keywords = {
            'jazz': ['jazz', 'bebop', 'swing', 'cool'],
            'rock': ['rock', 'riff', 'electric', 'grunge'],
            'classical': ['symphony', 'concerto', 'sonata', 'quartet'],
            'blues': ['blues', 'blues'],
            'pop': ['pop', 'chart'],
            'electronic': ['electronic', 'synth', 'drum'],
            'world': ['africa', 'latin', 'reggae', 'bossa']
        }
        
        track_titles = ' '.join([t.title.lower() for t in album.tracks])
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in track_titles for keyword in keywords):
                return genre
        
        return None
    
    def close(self):
        """Fermer la base de données"""
        self.db.close()

def enrich_all_albums():
    """Enrichir tous les albums sans images"""
    enricher = AlbumEnricher()
    
    try:
        albums_no_images = enricher.db.query(Album).filter(~Album.images.any()).all()
        
        print('\n🚀 ENRICHISSEMENT AUTOMATIQUE')
        print('='*70)
        print('Albums à enrichir: {}'.format(len(albums_no_images)))
        print('='*70)
        
        for idx, album in enumerate(albums_no_images):
            results = enricher.enrich_album(album)
            
            if results['images_added'] > 0 or results['errors']:
                status = '✅' if results['images_added'] > 0 else '⚠️'
                print('{} Album {} | {} | Images: +{}'.format(
                    status, album.id, album.title[:40], results['images_added']
                ))
            
            if (idx + 1) % 100 == 0:
                print('  ... {} albums traités'.format(idx + 1))
        
        print('\n' + '='*70)
        print('✅ Enrichissement terminé')
        print('='*70)
    
    finally:
        enricher.close()

if __name__ == '__main__':
    enrich_all_albums()
