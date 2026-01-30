"""Service EurIA pour la génération de contenu par IA."""
import httpx
from typing import Optional
import logging
import json

logger = logging.getLogger(__name__)


class AIService:
    """Client pour l'API EurIA (Infomaniak AI)."""
    
    def __init__(self, url: str, bearer: str, max_attempts: int = 5, default_error_message: str = "Aucune information disponible"):
        self.url = url
        self.bearer = bearer
        self.max_attempts = max_attempts
        self.default_error_message = default_error_message
    
    async def ask_for_ia(self, prompt: str, max_tokens: int = 500) -> str:
        """Poser une question à l'IA."""
        try:
            headers = {
                "Authorization": f"Bearer {self.bearer}",
                "Content-Type": "application/json"
            }
            
            # Modèle mistral3 pour l'API EurIA
            payload = {
                "model": "mistral3",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url,
                    headers=headers,
                    json=payload
                )
                
                # Log détaillé des erreurs
                if response.status_code >= 400:
                    error_text = response.text
                    logger.error(f"EurIA API Error {response.status_code}: {error_text}")
                    return self.default_error_message
                
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
                
                return self.default_error_message
                
        except Exception as e:
            logger.error(f"Erreur appel API EurIA: {e}")
            return self.default_error_message
    
    async def generate_album_info(self, artist_name: str, album_title: str) -> Optional[str]:
        """Générer une description d'album par IA (max 2000 caractères)."""
        prompt = f"""Tu es un expert musical. Décris l'album "{album_title}" de {artist_name}.

IMPORTANT : Ta réponse doit faire EXACTEMENT entre 1800 et 2000 caractères. Ne dépasse JAMAIS 2000 caractères. Termine proprement tes phrases, ne t'arrête pas au milieu d'une phrase.

Inclus dans ta description :
- Le contexte historique et culturel de l'album
- Le style musical et les influences
- Les thèmes principaux et l'atmosphère
- L'impact culturel et la réception
- Les morceaux marquants si pertinent
- L'héritage et l'influence sur la musique

Sois factuel, précis et captivant. Structure ton texte en paragraphes courts."""
        
        try:
            response = await self.ask_for_ia(prompt, max_tokens=750)
            
            # Seulement si vraiment nécessaire (sécurité)
            if len(response) > 2000:
                # Trouver la dernière phrase complète avant 2000 caractères
                truncated = response[:2000]
                last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
                if last_period > 1500:  # Si on trouve une phrase complète
                    response = response[:last_period + 1]
                else:
                    response = response[:1997] + "..."
            
            return response if response != self.default_error_message else None
            
        except Exception as e:
            logger.error(f"Erreur génération info album: {e}")
            return None
    
    async def generate_haiku(self, listening_data: dict) -> str:
        """Générer un haïku basé sur les données d'écoute."""
        prompt = f"""Tu es un poète spécialisé en haïkus. Crée un haïku qui capture l'essence des écoutes musicales suivantes:

Artistes principaux: {', '.join(listening_data.get('top_artists', [])[:5])}
Albums principaux: {', '.join(listening_data.get('top_albums', [])[:5])}
Nombre total d'écoutes: {listening_data.get('total_tracks', 0)}

Le haïku doit respecter la structure 5-7-5 syllabes et capturer l'ambiance musicale."""
        
        try:
            response = await self.ask_for_ia(prompt, max_tokens=100)
            return response
            
        except Exception as e:
            logger.error(f"Erreur génération haïku: {e}")
            return "Musique écoute / Notes qui dansent dans le temps / L'âme en harmonie"
    
    async def generate_playlist_by_prompt(self, prompt: str, available_tracks: list) -> list:
        """Générer une sélection de tracks basée sur un prompt."""
        tracks_context = "\n".join([
            f"{t['id']}: {t['artist']} - {t['title']} ({t['album']})"
            for t in available_tracks[:100]  # Limiter le contexte
        ])
        
        full_prompt = f"""Tu es un DJ expert. Sélectionne les meilleurs tracks pour créer une playlist correspondant à: "{prompt}"

Tracks disponibles:
{tracks_context}

Réponds uniquement avec les IDs des tracks séparés par des virgules (ex: 1,5,12,3). Sélectionne entre 20 et 30 tracks."""
        
        try:
            response = await self.ask_for_ia(full_prompt, max_tokens=200)
            
            # Parser les IDs
            track_ids = []
            for part in response.split(','):
                try:
                    track_id = int(part.strip())
                    if any(t['id'] == track_id for t in available_tracks):
                        track_ids.append(track_id)
                except ValueError:
                    continue
            
            return track_ids if track_ids else [t['id'] for t in available_tracks[:25]]
            
        except Exception as e:
            logger.error(f"Erreur génération playlist IA: {e}")
            return [t['id'] for t in available_tracks[:25]]
