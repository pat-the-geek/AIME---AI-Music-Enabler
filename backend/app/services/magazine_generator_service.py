"""Service pour la génération de magazines musicaux."""
import random
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Album, Artist, Track, ListeningHistory
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class MagazineGeneratorService:
    """Service pour générer des magazines musicaux dynamiques."""
    
    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
    
    def _get_artist_name(self, album: Album) -> str:
        """Obtenir le nom de l'artiste principal de l'album."""
        if album.artists:
            return ", ".join([a.name for a in album.artists])
        return "Unknown"
    
    def _get_fallback_content(self, album: Album, content_type: str) -> str:
        """Générer du contenu de remplissage quand l'IA échoue."""
        artist = self._get_artist_name(album)
        year = album.year or "?"
        
        fallback_templates = {
            "review": [
                f"*{album.title}* de {artist} est une œuvre remarquable. L'album capture une émotion brute et authentique, mêlant **technique impeccable** et *sensibilité musicale*. Une expérience d'écoute inoubliable.",
                f"{artist} nous offre avec *{album.title}* un **dialogue musical** subtil et profond. Chaque note semble avoir été placée avec intention, créant une atmosphère *captivante*.",
                f"Cet album de {artist} révèle une **maturation artistique** évidente. *{album.title}* conjugue innovation et tradition de façon **élégante** et *poétique*."
            ],
            "mood": [
                f"Une ambiance *envoûtante* et **intimiste**. {album.title} crée une *atmosphère* de rêverie contemplative. L'écoute ressemble à une **promenade nocturne** à travers les pensées intimes de l'âme.",
                f"**Intense** et *mélancolique*, cet album respire une profondeur émotionnelle rare. {artist} nous plonge dans un univers **introspectif** et *lumineux* à la fois.",
                f"*Apaisant* et **hypnotique**, {album.title} enveloppe l'auditeur dans une **brume sonore** délicate. Une méditation *musicale* pure et authentique."
            ],
            "story": [
                f"Imaginez une soirée d'été, les étoiles qui scintillent, et {artist} qui raconte sa vie à travers *{album.title}*. **Chaque titre** est un chapitre d'une histoire *profonde* et *universelle*.",
                f"La **narration musicale** de {artist} dans *{album.title}* évoque un voyage intérieur. De l'*aurore* du premier titre jusqu'au *crépuscule* du dernier, c'est une **quête de sens**.",
                f"Une **symphonie** de moments intimes. {album.title} raconte l'histoire d'une transformation *silencieuse* et *puissante*, celle de l'art qui touche l'âme."
            ],
            "technical": [
                f"*{album.title}* démontre une **production soignée** et une **arrangement** impeccable. La **clarté sonore** exceptionnelle révèle **chaque couche** de la composition. Une **masterclass** technique.",
                f"La **qualité d'enregistrement** exceptionnelle de cet album met en avant une **dynamique** impressionnante. {artist} a créé une **palette sonore** riche et **texturée**.",
                f"**Audacieux** dans ses choix de production, {album.title} révèle une **esthétique sonore** cohérente et **soignée**. Chaque **instrument** brille avec **clarté** et **présence**."
            ],
            "poetic": [
                f"*{album.title}* est une **poésie sonore**. {artist} peint avec des notes comme un poète avec des mots. Chaque son est une *strophe* délicate dans une **symphonie** d'émotions brutes.",
                f"Comme un **vers libre** mis en musique, cet album **danse** entre réalité et rêve. La *beauté* réside dans chaque **silence** et chaque **vibration** de l'âme.",
                f"Une **lyrique musicale** où les silences parlent aussi fort que les notes. {album.title} transcende le **quotidien** et nous touche à l'**essence même** de notre humanité."
            ],
            "haiku": [
                "Notes qui dansent\n**Harmonie** dans l'espace\nL'âme prend son vol",
                "Musique éternelle\n**Rythme** des cœurs secrets\nVie pure en chansons",
                "Sons qui résonnent\n**Lumière** dans le silence\nOublies éphémères",
                "Mélodies perdues\n**Échos** de nos souvenirs\nBeauté retrouvée",
                "Vibrations sonores\n**Magie** entre les instants\nL'infini enfin"
            ],
            "description": [
                f"Un album captivant de {artist} qui mêle tradition et innovation avec grâce.",
                f"{album.title} nous plonge dans une atmosphère unique, riche et profondément mouvante.",
                f"Une création artistique remarquable offrant une expérience sonore incontournable.",
                f"{artist} livre ici une œuvre sublime mêlant sensibilité et technique musicale raffinée.",
                f"Un album qui transcende le temps avec sa beauté intemporelle et son authenticité rare."
            ]
        }
        
        templates = fallback_templates.get(content_type, fallback_templates["review"])
        return random.choice(templates)
    
    
    async def _generate_layout_suggestion(self, page_type: str, content_description: str) -> Dict[str, Any]:
        """Demander à l'IA de suggérer un layout créatif et surprenant."""
        prompt = f"""Tu es un designer créatif de magazines musicaux d'avant-garde. Crée une mise en page AUDACIEUSE, ASYMÉTRIQUE et TOTALEMENT UNIQUE.

Type: {page_type}
Contenu: {content_description}

IMPORTANT:
- VARIE RADICALEMENT la position et taille des éléments à CHAQUE fois
- Les grandes images doivent être IMMENSES (jusqu'à 75% de l'écran)
- Alterne entre images minuscules et images géantes
- Crée des compositions DÉSÉQUILIBRÉES et SURPRENANTES
- CHANGE systématiquement l'agencement pour éviter toute répétition

Réponds UNIQUEMENT avec ce JSON (sans texte, sans markdown):
{{
  "columns": 1 ou 2 ou 3 ou 4 ou 5,
  "imagePosition": "left" ou "right" ou "top" ou "bottom" ou "center" ou "floating" ou "split" ou "diagonal" ou "corner" ou "fullwidth",
  "imageSize": "micro" ou "tiny" ou "small" ou "medium" ou "large" ou "huge" ou "massive" ou "fullscreen",
  "textLayout": "single" ou "double-column" ou "triple-column" ou "masonry" ou "asymmetric" ou "scattered" ou "vertical",
  "composition": "classic" ou "modern" ou "bold" ou "minimalist" ou "dramatic" ou "playful" ou "chaos" ou "zen" ou "magazine",
  "accentColor": "#couleur-hex-creative-vibrante",
  "specialEffect": "none" ou "gradient" ou "overlay" ou "frame" ou "shadow" ou "blur" ou "tilt" ou "zoom"
}}"""
        
        try:
            response = await self.ai_service.ask_for_ia(prompt, max_tokens=200)
            import json
            # Nettoyer la réponse
            response_clean = response.strip()
            if response_clean.startswith('```'):
                lines = response_clean.split('\n')
                response_clean = '\n'.join([l for l in lines if not l.startswith('```')])
            
            layout = json.loads(response_clean)
            return layout
        except Exception as e:
            logger.warning(f"⚠️ Erreur parsing layout IA: {e}")
            # Fallback ultra-varié avec forte randomisation
            positions = ["left", "right", "top", "bottom", "center", "floating", "split", "diagonal", "corner", "fullwidth"]
            sizes = ["micro", "tiny", "small", "medium", "large", "huge", "massive", "fullscreen"]
            layouts = ["single", "double-column", "triple-column", "masonry", "asymmetric", "scattered", "vertical"]
            compositions = ["classic", "modern", "bold", "minimalist", "dramatic", "playful", "chaos", "zen", "magazine"]
            colors = ["#667eea", "#764ba2", "#ff006e", "#00b4d8", "#ff6b35", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]
            effects = ["none", "gradient", "overlay", "frame", "shadow", "blur", "tilt", "zoom"]
            
            # Favoriser les tailles extrêmes pour plus de variété
            size_weights = [0.05, 0.1, 0.15, 0.15, 0.15, 0.15, 0.15, 0.1]  # Plus de chances pour huge/massive
            
            return {
                "columns": random.choice([1, 2, 2, 3, 3, 4, 5]),  # Favorise 2-3 colonnes
                "imagePosition": random.choice(positions),
                "imageSize": random.choices(sizes, weights=size_weights)[0],
                "textLayout": random.choice(layouts),
                "composition": random.choice(compositions),
                "accentColor": random.choice(colors),
                "specialEffect": random.choice(effects)
            }
    
    async def generate_magazine(self) -> Dict[str, Any]:
        """Générer un magazine complet avec 5 pages."""
        try:
            pages = []
            
            # Page 1: Artiste aléatoire + Albums récents
            try:
                page1 = await self._generate_page_1_artist()
                pages.append(page1)
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 1: {e}")
                pages.append(self._empty_page())
            
            # Page 2: Album du jour + Description longue
            try:
                page2 = await self._generate_page_2_album_detail()
                pages.append(page2)
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 2: {e}")
                pages.append(self._empty_page())
            
            # Page 3: Albums aléatoires + Haikus
            try:
                page3 = await self._generate_page_3_albums_haikus()
                pages.append(page3)
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 3: {e}")
                pages.append(self._empty_page())
            
            # Page 4: Timeline visuelle + Stats
            try:
                page4 = await self._generate_page_4_timeline()
                pages.append(page4)
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 4: {e}")
                pages.append(self._empty_page())
            
            # Page 5: Playlist thématique
            try:
                page5 = await self._generate_page_5_playlist()
                pages.append(page5)
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 5: {e}")
                pages.append(self._empty_page())
            
            # Randomiser l'ordre des pages pour effet de génération spontanée
            # Garder les page_numbers pour la navigation interne mais afficher dans ordre aléatoire
            shuffled_pages = pages.copy()
            random.shuffle(shuffled_pages)
            
            return {
                "id": f"magazine-{datetime.now().timestamp()}",
                "generated_at": datetime.now().isoformat(),
                "pages": shuffled_pages,
                "total_pages": len(shuffled_pages)
            }
        except Exception as e:
            logger.error(f"❌ Erreur génération magazine: {e}")
            raise
    
    async def _generate_page_1_artist(self) -> Dict[str, Any]:
        """Page 1: Artiste aléatoire + albums variés avec contenus IA diversifiés."""
        # Récupérer des artistes avec images
        artists = self.db.query(Artist).filter(
            Artist.images.any()
        ).all()
        
        if not artists:
            # Fallback : prendre n'importe quel artiste
            artists_count = self.db.query(func.count(Artist.id)).scalar()
            if artists_count == 0:
                return self._empty_page()
            offset = random.randint(0, max(0, artists_count - 1))
            artist = self.db.query(Artist).offset(offset).first()
        else:
            artist = random.choice(artists)
        
        if not artist or not artist.albums:
            return self._empty_page()
        
        # Récupérer albums avec images VALIDES en mode RANDOM au niveau SQL
        # Important: utiliser order_by(func.random()) pour vraie randomisation
        # Filtrer strictement: URL doit commencer par 'http'
        all_albums_with_images = self.db.query(Album).filter(
            Album.image_url.isnot(None),
            Album.image_url != '',
            Album.image_url.like('http%')  # Vérifier que c'est une vraie URL
        ).order_by(func.random()).limit(30).all()  # Random SQL + limite plus grande
        
        logger.info(f"Albums avec images valides trouvés: {len(all_albums_with_images)}")
        
        # Prendre 6-8 albums aléatoires (plus de variété)
        num_albums = min(random.randint(6, 8), len(all_albums_with_images))
        albums = all_albums_with_images[:num_albums]
        
        if not albums:
            return self._empty_page()
        
        # Générer un haiku créatif sur cet artiste
        haiku_prompt = f"Crée un haïku poétique (5-7-5 syllabes) sur l'essence musicale de {artist.name}. Sois émotionnel et évocateur. Réponds UNIQUEMENT avec le haïku en 3 lignes, sans numérotation."
        haiku = await self.ai_service.ask_for_ia(haiku_prompt, max_tokens=100)
        
        # Fallback pour le haiku
        if not haiku or haiku == "Aucune information disponible":
            haiku = random.choice([
                "Voix qui scintille\n**Âme** à travers les notes\nMagie immortelle",
                "Rythme du cœur vrai\n**Beauté** dans chaque instant\nLumière éternelle",
                "Notes qui résonnent\n**Esprit** libéré enfin\nMusique de l'âme"
            ])
        
        # Générer une description courte de l'artiste
        artist_bio_prompt = f"Génère une description courte et inspirante (50-80 mots) sur l'artiste {artist.name} et son style musical. Sois poétique et utilise du formatage markdown (gras, italique)."
        artist_bio = await self.ai_service.ask_for_ia(artist_bio_prompt, max_tokens=150)
        
        # Fallback pour la bio
        if not artist_bio or artist_bio == "Aucune information disponible":
            artist_bio = f"**{artist.name}** est un artiste visionnaire dont la musique transcende les genres. Sa **palette sonore** unique mêle *sensibilité* et *innovation*. Chaque composition raconte une histoire *profonde*, offrant aux auditeurs une **expérience intime** et *transformatrice*. Un créateur dont l'art inspire et **touche l'âme**."
        
        # Générer des contenus variés pour chaque album via l'IA
        albums_with_content = []
        content_types = ["review", "mood", "story", "technical", "poetic"]
        
        for album in albums:
            # Choisir aléatoirement un type de contenu
            content_type = random.choice(content_types)
            
            # Générer du contenu varié selon le type
            if content_type == "review":
                prompt = f"Écris une courte critique (60-80 mots) de l'album '{album.title}' de {self._get_artist_name(album)}. Utilise du markdown (gras, italique). Sois critique et profond."
            elif content_type == "mood":
                prompt = f"Décris l'ambiance et l'émotion (60-80 mots) de l'album '{album.title}' de {self._get_artist_name(album)}. Utilise du markdown. Sois évocateur."
            elif content_type == "story":
                prompt = f"Raconte une histoire courte (60-80 mots) inspirée par l'album '{album.title}' de {self._get_artist_name(album)}. Utilise du markdown. Sois narratif."
            elif content_type == "technical":
                prompt = f"Analyse la production et le son (60-80 mots) de l'album '{album.title}' de {self._get_artist_name(album)}. Utilise du markdown. Sois technique."
            else:  # poetic
                prompt = f"Écris une description poétique (60-80 mots) de l'album '{album.title}' de {self._get_artist_name(album)}. Utilise du markdown. Sois lyrique."
            
            ai_content = await self.ai_service.ask_for_ia(prompt, max_tokens=150)
            
            # Utiliser le fallback si l'IA retourne "Aucune information disponible"
            if ai_content == "Aucune information disponible" or not ai_content:
                ai_content = self._get_fallback_content(album, content_type)
            
            albums_with_content.append({
                "id": album.id,
                "title": album.title,
                "year": album.year,
                "image_url": album.image_url,
                "genre": album.genre,
                "artist": self._get_artist_name(album),
                "description": ai_content,
                "content_type": content_type
            })
            logger.info(f"Album ajouté: {album.title} - Image: {album.image_url[:50] if album.image_url else 'None'}")
        
        # Générer du contenu de remplissage pour espaces vides (citations, faits)
        filler_content = []
        for i in range(random.randint(2, 4)):
            filler_type = random.choice(["quote", "fact", "trivia"])
            try:
                if filler_type == "quote":
                    prompt = "Donne une citation courte (15-25 mots) d'un musicien célèbre. Retourne en markdown avec guillemets et auteur en *italique*."
                elif filler_type == "fact":
                    prompt = f"Écris un fait musical court (15-25 mots) sur {random.choice([a.genre for a in albums if a.genre])}. Format markdown."
                else:  # trivia
                    years = [a.year for a in albums if a.year]
                    year = random.choice(years) if years else 2000
                    prompt = f"Anecdote musicale (20-30 mots) sur l'année {year}. Format markdown."
                
                filler_text = await self.ai_service.ask_for_ia(prompt, max_tokens=60)
                if filler_text:
                    filler_content.append({
                        "type": filler_type,
                        "text": filler_text
                    })
            except Exception as e:
                logger.error(f"Erreur génération filler: {e}")
        
        # Demander à l'IA de suggérer un layout
        layout_suggestion = await self._generate_layout_suggestion(
            "artist_showcase",
            f"Artiste {artist.name} avec {len(albums)} albums variés et contenus créatifs diversifiés"
        )
        
        return {
            "page_number": 1,
            "type": "artist_showcase",
            "title": f"{artist.name}",
            "layout": layout_suggestion,
            "content": {
                "artist": {
                    "name": artist.name,
                    "albums_count": len(albums),
                    "haiku": haiku,
                    "bio": artist_bio,
                    "image_url": artist.images[0].url if artist.images else None
                },
                "albums": albums_with_content,
                "filler": filler_content  # Ajouter contenu de remplissage
            },
            "dimensions": {
                "image_height": random.choice([300, 400, 500, 600]),  # Varier les tailles
                "text_columns": layout_suggestion.get("columns", 2),
                "color_scheme": "newspaper"
            }
        }
    
    async def _generate_page_2_album_detail(self) -> Dict[str, Any]:
        """Page 2: Album du jour avec description longue."""
        # Récupérer un album aléatoire avec description IA
        albums = self.db.query(Album).filter(
            Album.ai_description.isnot(None)
        ).all()
        
        if not albums:
            return self._empty_page()
        
        album = random.choice(albums)
        artist_names = ", ".join([a.name for a in album.artists]) if album.artists else "Artiste inconnu"
        
        # Layout IA
        layout_suggestion = await self._generate_layout_suggestion(
            "album_detail",
            f"Album '{album.title}' avec description longue"
        )
        
        return {
            "page_number": 2,
            "type": "album_detail",
            "title": f"Album du Jour",
            "layout": layout_suggestion,
            "content": {
                "album": {
                    "id": album.id,
                    "title": album.title,
                    "artist": artist_names,
                    "year": album.year,
                    "genre": album.genre,
                    "image_url": album.image_url,
                    "description": album.ai_description,
                    "style": album.ai_style
                }
            },
            "dimensions": {
                "image_size": random.choice(["small", "medium", "large"]),
                "description_length": "full",
                "font_size": random.choice(["small", "medium", "large"])
            }
        }
    
    async def _generate_page_3_albums_haikus(self) -> Dict[str, Any]:
        """Page 3: Albums aléatoires + Haikus avec descriptions générées par l'IA."""
        # Sélectionner des albums avec images pour garantir des vignettes
        available_albums = self.db.query(Album).filter(
            Album.image_url.isnot(None)
        ).all()
        
        if len(available_albums) < 3:
            return self._empty_page()
        
        # Sélectionner 3-4 albums aléatoirement
        selected_albums = random.sample(available_albums, min(random.randint(3, 4), len(available_albums)))
        
        # Générer des haikus créatifs et descriptions variées pour chaque album
        haikus = []
        for album in selected_albums:
            # Générer un haïku unique
            haiku_prompt = f"Crée un haïku poétique (5-7-5 syllabes) sur l'album '{album.title}' de {self._get_artist_name(album)}. Sois créatif et émotionnel. Réponds UNIQUEMENT avec le haïku en 3 lignes, sans autre texte."
            haiku = await self.ai_service.ask_for_ia(haiku_prompt, max_tokens=100)
            
            # Utiliser fallback si l'IA échoue
            if haiku == "Aucune information disponible" or not haiku:
                haiku = self._get_fallback_content(album, "haiku")
            
            # Générer une description courte inspirée si pas existante
            description = album.ai_description
            if not description or description == "Aucune information disponible":
                desc_prompt = f"Génère une courte description (30 mots max) inspirante sur l'album '{album.title}' de {self._get_artist_name(album)}. Sois créatif et lyrique."
                description = await self.ai_service.ask_for_ia(desc_prompt, max_tokens=80)
            
            # Utiliser fallback si l'IA échoue
            if description == "Aucune information disponible" or not description:
                description = self._get_fallback_content(album, "description")
            
            # Générer un layout unique et varié pour chaque haiku
            individual_layout = await self._generate_layout_suggestion(
                "individual_haiku",
                f"Haïku poétique pour {album.title} de {self._get_artist_name(album)}"
            )
            haikus.append({
                "album_id": album.id,
                "album_title": album.title,
                "haiku": haiku,
                "layout": individual_layout,
                "description": description
            })
        
        # Layout IA pour la page
        layout_suggestion = await self._generate_layout_suggestion(
            "albums_haikus",
            f"{len(selected_albums)} albums avec haïkus et descriptions créatives"
        )
        
        return {
            "page_number": 3,
            "type": "albums_haikus",
            "title": "Haïkus Musicaux",
            "layout": layout_suggestion,
            "content": {
                "albums": [
                    {
                        "id": album.id,
                        "title": album.title,
                        "artist": ", ".join([a.name for a in album.artists]) if album.artists else "?",
                        "image_url": album.image_url,
                        "genre": album.genre
                    }
                    for album in selected_albums
                ],
                "haikus": haikus
            },
            "dimensions": {
                "image_size": random.choice(["small", "medium", "large"]),
                "columns": random.choice([1, 2, 3]),
                "spacing": random.choice(["compact", "normal", "spacious"])
            }
        }
    
    async def _generate_page_4_timeline(self) -> Dict[str, Any]:
        """Page 4: Timeline visuelle + Stats avec images artistes et albums."""
        # Récupérer les écoutes récentes
        recent_history = self.db.query(ListeningHistory).order_by(
            ListeningHistory.timestamp.desc()
        ).limit(50).all()
        
        if not recent_history:
            return self._empty_page()
        
        # Compter les artistes et albums
        artists_counter = {}
        albums_counter = {}
        
        for entry in recent_history:
            if entry.track and entry.track.album:
                album = entry.track.album
                albums_counter[album.id] = albums_counter.get(album.id, 0) + 1
                
                if album.artists:
                    for artist in album.artists:
                        artists_counter[artist.id] = artists_counter.get(artist.id, 0) + 1
        
        # Top artists et albums
        top_artists_ids = sorted(artists_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        top_albums_ids = sorted(albums_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Récupérer les objets complets avec images
        top_artists_full = []
        for artist_id, count in top_artists_ids:
            artist = self.db.query(Artist).filter(Artist.id == artist_id).first()
            if artist:
                top_artists_full.append({
                    "artist_id": artist.id,
                    "artist_name": artist.name,
                    "image_url": artist.images[0].url if artist.images else None,
                    "count": count
                })
        
        top_albums_full = []
        for album_id, count in top_albums_ids:
            album = self.db.query(Album).filter(Album.id == album_id).first()
            if album:
                top_albums_full.append({
                    "album_id": album.id,
                    "album_title": album.title,
                    "artist_name": self._get_artist_name(album),
                    "image_url": album.image_url,
                    "count": count
                })
        
        return {
            "page_number": 4,
            "type": "timeline_stats",
            "title": "Vos Dernières Écoutes",
            "layout": await self._generate_layout_suggestion("stats", "Top artistes et albums avec images"),
            "content": {
                "total_recent_listens": len(recent_history),
                "unique_artists": len(artists_counter),
                "unique_albums": len(albums_counter),
                "top_artists": top_artists_full,
                "top_albums": top_albums_full
            },
            "dimensions": {
                "chart_type": random.choice(["bar", "donut", "area"]),
                "color_scheme": "newspaper"
            }
        }
    
    async def _generate_page_5_playlist(self) -> Dict[str, Any]:
        """Page 5: Playlist thématique créative générée par l'IA avec albums variés."""
        # Récupérer les albums avec images (pour afficher les vignettes)
        albums = self.db.query(Album).filter(
            Album.image_url.isnot(None)
        ).limit(50).all()
        
        if len(albums) < 5:
            return self._empty_page()
        
        # Générer un thème créatif unique via l'IA
        theme_prompt = "Génère un titre de playlist musicale unique et créatif (5-8 mots max). Sois original et inspirati. Réponds UNIQUEMENT avec le titre, sans guillemets ni autre texte."
        selected_theme = await self.ai_service.ask_for_ia(theme_prompt, max_tokens=50)
        selected_theme = selected_theme.strip().strip('"')
        
        # Fallback pour le thème
        if not selected_theme or selected_theme == "Aucune information disponible":
            selected_theme = random.choice([
                "Échos Intimes",
                "Nuits Blanches",
                "Âmes Rêveuses",
                "Horizons Oubliés",
                "Symphonie des Cœurs",
                "Lumières Éternelles"
            ])
        
        # Générer une description accrocheuse pour la playlist
        playlist_prompt = f"Génère une description poétique et accrocheuse (80-120 mots) pour une playlist intitulée '{selected_theme}'. Inspire l'écoute musicale."
        playlist_description = await self.ai_service.ask_for_ia(playlist_prompt, max_tokens=200)
        
        # Fallback pour la description
        if not playlist_description or playlist_description == "Aucune information disponible":
            playlist_description = f"*{selected_theme}* est une playlist curated avec soin, mêlant **mélodies intemporelles** et *productions modernes*. Chaque album a été sélectionné pour son **pouvoir émotionnel** et son *authenticité artistique*. Plongez-vous dans cette **expérience sonore** unique et laissez la musique vous **transporter** vers des univers *nouveaux* et *captivants*."
        
        # Sélectionner 5-7 albums de manière vraiment aléatoire
        num_albums = random.randint(5, min(7, len(albums)))
        selected_albums = random.sample(albums, num_albums)
        
        playlist_albums = []
        for album in selected_albums:
            # Générer une raison IA pour chaque album (pourquoi il est dans cette playlist)
            reason_prompt = f"Propose une phrase courte (10-20 mots) expliquant pourquoi l'album '{album.title}' de {self._get_artist_name(album)} est parfait pour '{selected_theme}'. Sois poétique et inspirant."
            album_reason = await self.ai_service.ask_for_ia(reason_prompt, max_tokens=50)
            
            # Fallback pour la raison
            if not album_reason or album_reason == "Aucune information disponible":
                album_reason = random.choice([
                    f"**Captivant** et *authentique*, cet album incarne l'essence de *{selected_theme}*.",
                    f"Une **sélection poétique** qui résonne parfaitement avec le thème de cette playlist.",
                    f"*{album.title}* apporte une **profondeur émotionnelle** incomparable à cette playlist.",
                    f"**Incontournable** pour ceux qui recherchent l'*authenticité* musicale.",
                    f"Un album qui **transcende** et offre une nouvelle *perspective* sonore."
                ])
            
            # Générer un layout unique pour chaque album
            album_layout = await self._generate_layout_suggestion(
                "playlist_album",
                f"Album {album.title} de {self._get_artist_name(album)} pour playlist {selected_theme}"
            )
            playlist_albums.append({
                "id": album.id,
                "title": album.title,
                "artist": ", ".join([a.name for a in album.artists]) if album.artists else "?",
                "image_url": album.image_url,
                "year": album.year,
                "layout": album_layout,
                "reason": album_reason
            })
        
        return {
            "page_number": 5,
            "type": "playlist_theme",
            "title": f"Playlist: {selected_theme}",
            "layout": await self._generate_layout_suggestion("playlist_page", f"Playlist créative: {selected_theme}"),
            "content": {
                "playlist": {
                    "theme": selected_theme,
                    "description": playlist_description,
                    "albums": playlist_albums
                }
            },
            "dimensions": {
                "card_style": random.choice(["minimal", "detailed", "artistic"]),
                "image_position": random.choice(["left", "top", "background"])
            }
        }
    
    def _empty_page(self) -> Dict[str, Any]:
        """Retourner une page vide."""
        return {
            "page_number": 0,
            "type": "empty",
            "title": "Page vide",
            "layout": "empty",
            "content": {}
        }
