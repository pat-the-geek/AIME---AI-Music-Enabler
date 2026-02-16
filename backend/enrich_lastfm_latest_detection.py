import asyncio
from app.database import SessionLocal
from app.models import ListeningHistory, Album, Artist, Track, Image, Metadata
from app.services.lastfm_service import LastFMService
from app.services.spotify_service import SpotifyService
from app.services.apple_music_service import AppleMusicService
from app.services.external.ai_service import AIService
from app.core.config import get_settings
import os
import sys

async def enrich_lastfm_latest_detection():
    print("[DEBUG] Script enrich_lastfm_latest_detection.py démarré", flush=True)
    
    # Charger la configuration
    settings = get_settings()
    secrets = settings.secrets
    
    print(f"[DEBUG] Configuration chargée, clés disponibles: {list(secrets.keys())}", flush=True)
    
    session = SessionLocal()
    try:
        print("[DEBUG] Recherche des deux dernières détections Last.fm...", flush=True)
        lastfm_entries = session.query(ListeningHistory)\
            .filter(ListeningHistory.source == 'lastfm')\
            .order_by(ListeningHistory.timestamp.desc())\
            .limit(2).all()
        print(f"[DEBUG] lastfm_entries trouvées: {len(lastfm_entries)}", flush=True)
        if not lastfm_entries:
            print("Aucune détection Last.fm trouvée.", flush=True)
            return

        # Charger les secrets depuis la configuration
        lastfm_config = secrets.get('lastfm', {})
        spotify_config = secrets.get('spotify', {})
        
        lastfm_api_key = lastfm_config.get('api_key')
        lastfm_api_secret = lastfm_config.get('api_secret')
        lastfm_username = lastfm_config.get('username')
        
        print(f"[DEBUG] Last.fm API key chargée: {bool(lastfm_api_key)}", flush=True)
        if lastfm_api_key:
            print(f"[DEBUG] Last.fm API key: {lastfm_api_key[:5]}...{lastfm_api_key[-5:]}", flush=True)
        print(f"[DEBUG] Last.fm API secret chargée: {bool(lastfm_api_secret)}", flush=True)
        print(f"[DEBUG] Last.fm username chargé: {bool(lastfm_username)} ({lastfm_username if lastfm_username else 'N/A'})", flush=True)
        
        spotify_client_id = spotify_config.get('client_id')
        spotify_client_secret = spotify_config.get('client_secret')
        
        print(f"[DEBUG] Spotify client_id chargé: {bool(spotify_client_id)}", flush=True)
        if spotify_client_id:
            print(f"[DEBUG] Spotify client_id: {spotify_client_id[:5]}...{spotify_client_id[-5:]}", flush=True)
        print(f"[DEBUG] Spotify client_secret chargé: {bool(spotify_client_secret)}", flush=True)
        
        lastfm_service = LastFMService(
            api_key=lastfm_api_key,
            api_secret=lastfm_api_secret,
            username=lastfm_username
        )
        spotify_service = SpotifyService(client_id=spotify_client_id, client_secret=spotify_client_secret)
        ai_service = AIService()

        for lastfm_entry in lastfm_entries:
            track = session.query(Track).filter_by(id=lastfm_entry.track_id).first()
            album = session.query(Album).filter_by(id=track.album_id).first() if track else None
            artist = session.query(Artist).filter_by(id=album.artists[0].id).first() if album and album.artists else None

            # 2. Récupérer le vrai artiste de l'album
            artist_name = artist.name if artist else ''
            album_title = album.title if album else ''
            print(f"[DEBUG] Paramètres pour enrichissement: artist_name='{artist_name}', album_title='{album_title}'", flush=True)
            print(f"[DEBUG] IDs en base: track_id={lastfm_entry.track_id}, album_id={album.id if album else None}, artist_id={artist.id if artist else None}", flush=True)
            
            if not artist_name or not album_title:
                print(f"[ERREUR] artist_name ou album_title vide, détection ignorée (ID: {lastfm_entry.id})", flush=True)
                continue
            
            # **NETTOYER LES IMAGES SPOTIFY DÈS LE DÉBUT** 
            # S'assurer que seule Last.fm est utilisée pour les albums Last.fm
            if album:
                spotify_images = session.query(Image).filter_by(album_id=album.id, image_type='album', source='spotify').all()
                if spotify_images:
                    print(f"[DEBUG] ⚠️ Suppression de {len(spotify_images)} images Spotify avant traitement...", flush=True)
                    for old_img in spotify_images:
                        session.delete(old_img)
                    session.flush()
            
            # Afficher l'état initial de l'image d'album
            initial_img = session.query(Image).filter_by(album_id=album.id, image_type='album').first() if album else None
            print(f"[DEBUG] Image initiale: {initial_img.url if initial_img else 'Aucune'}", flush=True)
            
            album_artists = await lastfm_service.get_album_artists(artist_name, album_title)
            main_artist_name = album_artists[0] if album_artists else artist_name
            if artist and main_artist_name and main_artist_name != artist.name:
                artist.name = main_artist_name
                session.commit()
                print(f"Artiste mis à jour: {main_artist_name}", flush=True)
            
            # Mettre à jour le support si l'album n'est pas de Discogs et n'a pas de support défini
            if album and album.source != 'discogs' and not album.support:
                album.support = 'Lastfm'
                session.commit()
                print(f"[DEBUG] Support album mis à jour à 'Lastfm'", flush=True)
            elif album:
                print(f"[DEBUG] Support album non modifié: source={album.source}, support={album.support}", flush=True)

            # 3. Vérifier/corriger l'image de l'album
            print(f"Recherche image Spotify pour: artiste='{main_artist_name}', album='{album_title}'", flush=True)
            album_image_spotify = None
            try:
                print(f"[DEBUG] Appel Spotify avec: artiste='{main_artist_name}' (len={len(main_artist_name)}), album='{album_title}' (len={len(album_title)})", flush=True)
                album_details_spotify = await spotify_service.search_album_details(main_artist_name, album_title)
                print("album_details_spotify brut:", repr(album_details_spotify), flush=True)
                if album_details_spotify and album_details_spotify.get("image_url"):
                    def normalize(s):
                        return ''.join(s.lower().split()) if s else ''
                    found_album = album_details_spotify.get("name") or album_details_spotify.get("album_title") or album_title
                    found_artist = None
                    if "artists" in album_details_spotify and album_details_spotify["artists"]:
                        found_artist = album_details_spotify["artists"][0].get("name", main_artist_name)
                    else:
                        found_artist = album_details_spotify.get("artist_name") or main_artist_name
                    print(f"Comparaison stricte: attendu album='{album_title}', trouvé='{found_album}' | attendu artiste='{main_artist_name}', trouvé='{found_artist}'", flush=True)
                    if normalize(found_album) == normalize(album_title) and normalize(found_artist) == normalize(main_artist_name):
                        album_image_spotify = album_details_spotify["image_url"]
                        print(f"Image Spotify validée: {album_image_spotify}", flush=True)
                    else:
                        print(f"Image Spotify ignorée (mauvais album/artiste): album='{found_album}', artiste='{found_artist}'", flush=True)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print(f"[ERREUR] Exception Spotify: {type(e).__name__}: {e}", flush=True)
                print(f"[DEBUG] Traceback complet:\n{tb}", flush=True)

            print(f"Recherche image Last.fm pour: artiste='{main_artist_name}', album='{album_title}'", flush=True)
            album_image_lastfm = None
            try:
                print(f"[DEBUG] Appel Last.fm avec: artiste='{main_artist_name}' (len={len(main_artist_name)}), album='{album_title}' (len={len(album_title)})", flush=True)
                album_image_lastfm = await lastfm_service.get_album_image(main_artist_name, album_title)
                print(f"Résultat image Last.fm: {album_image_lastfm}", flush=True)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print(f"[ERREUR] Exception Last.fm: {type(e).__name__}: {e}", flush=True)
                print(f"[DEBUG] Traceback complet:\n{tb}", flush=True)

            # Exception : si aucune image Spotify trouvée, utiliser explicitement Last.fm
            # PRIORITÉ: Last.fm en premier (meilleure qualité), puis Spotify en fallback
            if album_image_lastfm:
                image_url = album_image_lastfm
                image_source = 'lastfm'
            elif album_image_spotify:
                image_url = album_image_spotify
                image_source = 'spotify'
            else:
                image_url = None
                image_source = None
            
            if album and image_url:
                print(f"[DEBUG] Avant mise à jour: album.image_url={album.image_url}", flush=True)
                
                # Supprimer TOUTES les images Spotify pour cet album (garder que Last.fm)
                if image_source == 'lastfm':
                    spotify_images = session.query(Image).filter_by(album_id=album.id, image_type='album', source='spotify').all()
                    if spotify_images:
                        print(f"[DEBUG] Suppression de {len(spotify_images)} images Spotify", flush=True)
                        for old_img in spotify_images:
                            session.delete(old_img)
                        session.flush()
                
                # Récupérer ou créer l'image
                img = session.query(Image).filter_by(album_id=album.id, image_type='album', source=image_source).first()
                if img:
                    print(f"[DEBUG] Image {image_source} existante trouvée (id={img.id}), mise à jour...", flush=True)
                    img.url = image_url
                else:
                    print(f"[DEBUG] Aucune image {image_source} existante, création d'une nouvelle...", flush=True)
                    img = Image(url=image_url, image_type='album', source=image_source, album_id=album.id)
                    session.add(img)
                
                # Correction : mettre à jour aussi album.image_url
                album.image_url = image_url
                session.flush()  # Flush avant commit pour obtenir l'id de la nouvelle image
                session.commit()
                print(f"[DEBUG] Après commit: album.image_url={album.image_url}", flush=True)
                print(f"Image d'album mise à jour ({image_source}): {image_url}", flush=True)
                
                # Vérification que l'image est bien en base
                verify_img = session.query(Image).filter_by(album_id=album.id, image_type='album').first()
                print(f"[DEBUG] Vérification après commit: image_url en base={verify_img.url if verify_img else 'AUCUNE'}", flush=True)
            else:
                print(f"[WARNING] Pas de mise à jour image (album={album}, image_url={image_url})", flush=True)

            # 4. Mettre à jour metadata IA
            ai_info = await ai_service.generate_album_info(main_artist_name, album_title)
            if album and ai_info:
                metadata = session.query(Metadata).filter_by(album_id=album.id).first()
                if metadata:
                    print(f"[DEBUG] Métadonnées existantes trouvées (id={metadata.id}), mise à jour...", flush=True)
                    metadata.ai_info = ai_info
                else:
                    print(f"[DEBUG] Aucune métadonnée existante, création d'une nouvelle...", flush=True)
                    metadata = Metadata(album_id=album.id, ai_info=ai_info)
                    session.add(metadata)
                session.flush()
                session.commit()
                print(f"[DEBUG] Métadonnées sauvegardées avec succès", flush=True)
                print("Metadata IA mise à jour.", flush=True)
            else:
                print(f"[WARNING] Pas de mise à jour métadonnées (album={album}, ai_info={ai_info is not None})", flush=True)

            print(f"✅ Détection Last.fm enrichie (ID: {lastfm_entry.id})", flush=True)
    
    finally:
        print("[DEBUG] Fermeture de la session...", flush=True)
        session.close()
        print("[DEBUG] Session fermée", flush=True)


# Ajout de l'appel principal pour exécuter la fonction asynchrone
if __name__ == "__main__":
    import asyncio
    asyncio.run(enrich_lastfm_latest_detection())
    
    # Vérification finale en requêtant la base de données
    print("[DEBUG] Vérification finale des données sauvegardées...", flush=True)
    final_session = SessionLocal()
    try:
        lastfm_entries = final_session.query(ListeningHistory)\
            .filter(ListeningHistory.source == 'lastfm')\
            .order_by(ListeningHistory.timestamp.desc())\
            .limit(2).all()
        
        for entry in lastfm_entries:
            track = final_session.query(Track).filter_by(id=entry.track_id).first()
            album = final_session.query(Album).filter_by(id=track.album_id).first() if track else None
            if album:
                img = final_session.query(Image).filter_by(album_id=album.id, image_type='album').first()
                print(f"[VÉRIFICATION] Album '{album.title}': image_url en base = {album.image_url[:50]}..." if album.image_url else f"[VÉRIFICATION] Album '{album.title}': image_url = None", flush=True)
                print(f"[VÉRIFICATION] Image table (id={img.id if img else None}): url = {img.url[:50]}..." if img and img.url else f"[VÉRIFICATION] Image table: AUCUNE", flush=True)
    finally:
        final_session.close()
    
    print("[DEBUG] Script terminé avec succès ✅", flush=True)
