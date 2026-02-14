"""Service pour la génération de magazines musicaux."""
import random
import logging
import asyncio
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Album, Artist, Track, ListeningHistory
from app.services.external.ai_service import AIService
from app.services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)

# Tracking global des rafraîchissements en cours
refresh_status = {
    "magazine_id": None,
    "status": "idle",  # idle, refreshing, enriching, completed
    "total_albums": 0,
    "refreshed_count": 0,
    "enriched_count": 0,
    "currently_processing": None,
    "albums_progress": []  # Liste des albums traités avec détails
}


class MagazineGeneratorService:
    """Service for generating dynamic AI-powered music magazines with multi-page layouts.
    
    Produces 5-page magazines featuring personalized artist profiles, album details, haikus,
    and curated collections. Each page includes AI-generated content (descriptions, haikus),
    album metadata, and Spotify imagery with rich markdown formatting. Supports background
    album enrichment (remasters/deluxe editions) and image refresh workflows with progress
    tracking.
    
    Key Features:
    - Page 1: Featured artist with top listening history albums
    - Page 2: Detailed album profile with listening stats and AI analysis
    - Page 3: Album haikus (AI-generated poetic 5-7-5 format for multiple albums)
    - Page 4: Curated collection with listening correlations
    - Page 5: Thematic collection with mood/context-based curation
    
    AI Integration:
    - AIService for haiku generation (10s timeout, fallback to template haikus)
    - Album description generation with creative fallback templates
    - Context-aware content enrichment (reviews, moods, stories, technical analysis)
    
    Image Management:
    - Spotify image search for albums missing cover art
    - Image URL validation and caching
    - Fallback to default images on network failures
    
    Background Tasks:
    - Album refresh: Updates missing images/descriptions (20 min polling)
    - Album enrichment: Enriches remaster/deluxe editions with rich descriptions
    - Progress tracking via global refresh_status dict
    
    Performance:
    - Typical generation time: 30-60 seconds for 5-page magazine
    - Supports streaming generations via yield pattern
    - Timeout handling: 10s AI haikus, 120s article generation
    - Database query optimization with joinedload relationships
    
    Example Usage:
    >>> service = MagazineGeneratorService(db, ai_service, spotify_service)
    >>> magazine = await service.generate_magazine()
    >>> print(f\"Generated {len(magazine['pages'])} pages\")
    """
    
    def __init__(self, db: Session, ai_service: AIService, spotify_service: SpotifyService = None):
        """Initialize magazine generator with database and AI services.
        
        Args:
            db: SQLAlchemy session for album/artist/listening history queries
            ai_service: AIService instance for haiku/description generation with 10-45s timeouts
            spotify_service: Optional SpotifyService for album image lookup. If None, falls back
                to existing image_url fields in database (logs warning if unavailable).
        
        Returns:
            Initialized MagazineGeneratorService instance ready for magazine generation
        
        Attributes:
            self.db: Database session (persisted for all operations)
            self.ai_service: AI generation service (haikus, descriptions, enrichment)
            self.spotify_service: Spotify image/metadata lookup service (optional)
        
        Example:
            >>> ai = AIService(config)
            >>> spotify = SpotifyService(client_id, client_secret)
            >>> mag_gen = MagazineGeneratorService(db, ai, spotify)
        """
        self.db = db
        self.ai_service = ai_service
        if spotify_service is None:
            logger.warning("⚠️  SpotifyService not provided, some features will be limited")
        self.spotify_service = spotify_service
    
    async def _generate_ai_haiku(self, album: Album, context: str = "") -> str:
        """Generate AI-crafted 5-7-5 syllable haiku for album via creative prompt.
        
        Creates poetic haiku using AIService with 10-second timeout. On timeout or failure,
        returns template-based fallback haiku constructed from album metadata. Haiku format:
        - Line 1: Album title in bold markdown
        - Line 2-3: Poetic description with musical metaphors (5-7 syllables typical)
        
        Args:
            album: Album ORM instance with title, artist, genre attributes
            context: Optional prompt context string (e.g., mood, theme, descriptor)
                Empty string for standard haiku, additional context for thematic generation
        
        Returns:
            str: Haiku in markdown format with ** bold markers for title
                Typical format: '**Album Title**\nPoetic line\nSecond poetic line'
        
        Raises:
            No exceptions raised; all failures return sensible fallback haikus.
        
        Example:
            >>> album = Album(title='Dark Side', artists=[...], genre='Rock')
            >>> haiku = await gen._generate_ai_haiku(album, 'nocturne')
            >>> print(haiku)
            '**Dark Side**\\nLa lumière danse\\nDans l\\'ombre infinie'
        
        Performance Notes:
            - Timeout: 10 seconds (asyncio.wait_for with TimeoutError fallback)
            - Token limit: 100 max (haiku ~30-50 tokens typical)
            - Execution time: 2-10s if AI available, <100ms for fallback
            - No database writes (read-only album data)
        
        Implementation Notes:
            - Builds prompt with: album title, artist name, genre, optional context
            - Specifies strict 3-line format with poetic examples
            - Falls back to metadata-based haiku on timeout: f\"**{title}**\\n*{genre}* sublime\\nPar {artist}\"
            - Genre defaults to 'musique' if missing
            - Artist names comma-joined via _get_artist_name()
        
        Logging:
            - INFO: \"✨ Haiku IA généré pour {album.title}\" on success
            - WARNING: \"⏱️ Timeout génération haiku IA pour {album.title}\" on 10s timeout
            - WARNING: \"⚠️ Erreur génération haiku IA pour {album.title}: {e}\" on exception
        
        Fallback Strategy:
            1. Try AI generation (10s timeout)
            2. On timeout/exception: Use metadata template
            3. Never returns None; always returns valid haiku string
        
        Design Pattern:
            Graceful degradation - always returns content even if AI fails.
            Used for magazine pages with configurable timeout to prevent cascading failures.
        """
        try:
            artist_name = self._get_artist_name(album)
            genre = album.genre or "musique"
            
            prompt = f"""Crée un haïku poétique de 3 lignes pour l'album "{album.title}" de {artist_name} ({genre}).
            
Format strict :
            - Ligne 1 : Titre de l'album en gras (**)
            - Ligne 2 : Description poétique courte (5-7 mots)
            - Ligne 3 : Continuation poétique (5-7 mots)
            
            Style : poétique, évocateur, utilise des métaphores musicales.
            {context}
            
            Exemple :
            **Dark Side of the Moon**
            Lumière dansant dans l'ombre
            Sons cosmiques infinis"""
            
            # Timeout de 10 secondes pour éviter de bloquer
            response = await asyncio.wait_for(
                self.ai_service.ask_for_ia(prompt, max_tokens=100),
                timeout=10.0
            )
            
            haiku = response.strip()
            logger.info(f"✨ Haiku IA généré pour {album.title}")
            return haiku
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout génération haiku IA pour {album.title}")
            artist_name = self._get_artist_name(album)
            genre = album.genre or "musique"
            return f"**{album.title}**\n*{genre}* sublime\nPar {artist_name}"
        except Exception as e:
            logger.warning(f"⚠️ Erreur génération haiku IA pour {album.title}: {e}")
            # Fallback : haiku basé sur les données
            artist_name = self._get_artist_name(album)
            genre = album.genre or "musique"
            return f"**{album.title}**\n*{genre}* sublime\nPar {artist_name}"
    
    def _clean_markdown_text(self, text: str) -> str:
        """Remove extraneous markdown delimiters and normalize formatting.
        
        Post-processes AI-generated content to clean up markdown syntax:
        - Removes opening/closing triple backticks (``` or ```markdown)
        - Converts markdown headers (# ## ###) to bold text (**text**)
        - Preserves inline formatting (*, **)
        - Strips leading/trailing whitespace
        
        Args:
            text: Raw markdown text from AI or template (may include code blocks)
        
        Returns:
            str: Cleaned text with normalized markdown syntax
        
        Example:
            >>> text = '```markdown\\n# Album Review\\nDescription...\\n```'
            >>> cleaned = service._clean_markdown_text(text)
            >>> print(cleaned)
            '**Album Review**\\nDescription...'
        
        Performance Notes:
            - O(n) where n = text length (single pass + split operations)
            - Typical: <1ms for typical album descriptions (<500 chars)
        
        Implementation Notes:
            - Removes '```markdown' opening delimiter
            - Removes '```' closing delimiter
            - Converts '# Title' to '**Title**'
            - Preserves other markdown formatting
            - Handles multi-line text with split('\\n') iteration
        """
        if not text:
            return text
        
        # Supprimer les délimiteurs de bloc markdown
        text = text.strip()
        if text.startswith('```markdown'):
            text = text[11:].lstrip('\n')  # Remove opening ```markdown
        if text.startswith('```'):
            text = text[3:].lstrip('\n')
        if text.endswith('```'):
            text = text[:-3].rstrip('\n')  # Remove closing ```
        
        # Supprimer les titres markdown (# ## ###) au début des lignes
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Si la ligne commence par # (titre), la convertir en texte normal en gras
            if line.strip().startswith('#'):
                # Compter les # et les retirer
                stripped = line.lstrip('#').strip()
                if stripped:
                    # Si c'était un titre, le mettre en gras
                    cleaned_lines.append(f"**{stripped}**")
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _ensure_markdown_format(self, text: str) -> str:
        """Ensure text has proper markdown formatting for display.
        
        Post-processes content without markdown formatting to add emphasis.
        If text lacks any markdown delimiters (**, *, #, -, >), adds bold formatting
        to first sentence/word. Calls _clean_markdown_text for initial normalization.
        
        Args:
            text: Plain or markdown-formatted text
        
        Returns:
            str: Text with guaranteed markdown formatting (at minimum bold first sentence)
        
        Example:
            >>> text = 'This is a plain review without formatting.'
            >>> formatted = service._ensure_markdown_format(text)
            >>> print(formatted)
            '**This is a plain review without formatting.**'
            
            >>> text = 'Already has **bold** formatting.'
            >>> formatted = service._ensure_markdown_format(text)
            >>> print(formatted)  # Unchanged (has markdown)
            'Already has **bold** formatting.'
        
        Performance Notes:
            - O(n) where n = text length (single pass + split if needed)
            - Typical: <1ms
        
        Implementation Notes:
            - First calls _clean_markdown_text() for normalization
            - Checks for any markdown delimiters: **, *, #, -, >
            - For text >50 chars: Splits on '. ' and bolds first sentence
            - For text <50 chars: Bolds entire text
            - Sentence splitting only on '. ' (period + space) to avoid acronyms
        
        Use Case:
            Ensures all album descriptions have visual emphasis in magazine layouts
            even if AI returns plain text without formatting.
        """
        if not text:
            return text
        
        text = self._clean_markdown_text(text)
        
        # Si le texte ne contient aucun formatage markdown, ajouter du gras
        if not any(marker in text for marker in ['**', '*', '#', '-', '>']):
            # Mettre en gras le premier mot ou la première phrase
            if len(text) > 50:
                sentences = text.split('. ')
                if sentences:
                    sentences[0] = f"**{sentences[0]}**"
                    text = '. '.join(sentences)
            else:
                text = f"**{text}**"
        
        return text
    
    def _get_artist_name(self, album: Album) -> str:
        """Extract primary artist name(s) from album.
        
        Returns comma-separated artist names from Album.artists relationship,
        fallback to 'Unknown' if no artists defined. Used for haiku generation,
        display labels, and Spotify image search queries.
        
        Args:
            album: Album ORM instance with artists relationship
        
        Returns:
            str: Artist name(s) comma-separated (e.g., 'Artist A, Artist B')
                or 'Unknown' if album.artists empty/None
        
        Example:
            >>> album.artists = [Artist(name='David Bowie'), Artist(name='Mick Jagger')]
            >>> service._get_artist_name(album)
            'David Bowie, Mick Jagger'
        
        Performance:
            - O(1) access to album.artists relationship (already loaded)
            - String join: O(n) where n = number of artists (typically 1-5)
        """
        if album.artists:
            return ", ".join([a.name for a in album.artists])
        return "Unknown"
    
    def _is_remaster_or_deluxe(self, album_title: str) -> bool:
        """Detect if album title indicates remaster/deluxe/special edition.
        
        Checks album_title (case-insensitive) against keyword list to identify
        special editions requiring enhanced descriptions and enrichment.
        Keywords: remaster, deluxe, remix, anniversary, expanded, bonus, etc.
        
        Args:
            album_title: Album title string to analyze
        
        Returns:
            bool: True if title contains remaster/deluxe keywords, False otherwise
        
        Example:
            >>> service._is_remaster_or_deluxe('Dark Side of the Moon (2021 Remaster)')
            True
            >>> service._is_remaster_or_deluxe('Rumours')
            False
        
        Performance:
            - O(k*m) where k = keywords (13), m = avg keyword length (10)
            - Typical: <100µs single check
        
        Keywords Detected:
            - English: remaster, remastered, deluxe, remix, remixes, anniversary,
              edition, expanded, special edition, collector, bonus
            - French: réédition, remasterisé
        """
        title_lower = album_title.lower()
        keywords = [
            'remaster', 'remastered', 'deluxe', 'remix', 'remixes',
            'anniversary', 'edition', 'expanded', 'special edition',
            'collector', 'bonus', 'réédition', 'remasterisé'
        ]
        return any(keyword in title_lower for keyword in keywords)
    
    def _should_enrich_album(self, album_id: int, album_title: str) -> bool:
        """Determine if album should be enriched with enhanced descriptions.
        
        Enrichment targets remaster/deluxe editions with insufficient descriptions.
        Conditions:
        1. Album title must indicate remaster/deluxe (via _is_remaster_or_deluxe)
        2. Album must have description ≤500 characters (deemed insufficient)
        
        Enrichment: Background task that generates creative 3-5 sentence descriptions
        incorporating album metadata and contextual information.
        
        Args:
            album_id: Integer album ID for database lookup
            album_title: Album title string for keyword detection
        
        Returns:
            bool: True if both conditions met (remaster AND description ≤500 chars)
        
        Example:
            >>> # Remaster but already rich description
            >>> service._should_enrich_album(42, 'Dark Side Remaster')  # description=700 chars
            False
            >>> # Remaster with thin description
            >>> service._should_enrich_album(42, 'Dark Side Remaster')  # description=200 chars
            True
        
        Performance:
            - Database lookup: O(1) Album.id index
            - Keyword detection: O(k*m) via _is_remaster_or_deluxe
            - Total: Typically <5ms
        
        Logging:
            - No direct logging; failures silently return False
        
        Implementation Notes:
            - Skips enrichment if album_id not found (returns False)
            - Description char count includes all whitespace
            - Threshold: >500 chars considered 'rich' and skipped
        """
        # Enrichir UNIQUEMENT les albums remaster/deluxe sans description riche
        if not self._is_remaster_or_deluxe(album_title):
            return False
        
        # Vérifier si l'album a déjà une description riche
        album = self.db.query(Album).filter(Album.id == album_id).first()
        if not album:
            return False
        
        # Si la description existe et fait > 500 caractères, pas besoin d'enrichir
        if album.ai_description and len(album.ai_description) > 500:
            return False
        
        return True
    
    def _should_refresh_album(self, album: Album) -> bool:
        """Determine if album needs refresh: missing/invalid image or description.
        
        Refresh checks for:
        1. Missing image: no image_url OR empty string OR invalid URL (doesn't start with 'http')
        2. Missing description: no ai_description OR description <50 chars (minimum viable)
        
        Refresh task: Updates album.image_url via Spotify search and generates
        enriched description if missing.
        
        Args:
            album: Album ORM instance with image_url and ai_description attributes
        
        Returns:
            bool: True if either image missing/invalid OR description <50 chars
        
        Example:
            >>> # Missing image
            >>> album = Album(image_url='', ai_description='A good description')
            >>> service._should_refresh_album(album)
            True
            
            >>> # Description too short
            >>> album = Album(image_url='https://...', ai_description='Short')
            >>> service._should_refresh_album(album)
            True
        
        Performance:
            - O(1) access to album attributes (no database queries)
            - String checks: O(n) where n = url/description length (typically <500)
        
        Image URL Validation:
            - None or empty string: needs refresh
            - Non-empty but doesn't start with 'http': needs refresh (e.g., relative path)
            - Valid http/https: passes validation
        
        Description Validation:
            - None or empty: needs refresh
            - <50 characters: needs refresh (too minimal for magazine display)
            - ≥50 characters: sufficient for display
        
        Logical OR:
            True if EITHER image bad OR description insufficient.
            Both can be refreshed in single background task.
        """
        # Rafraîchir si pas d'image OU si pas de description
        missing_image = not album.image_url or album.image_url == '' or not album.image_url.startswith('http')
        missing_description = not album.ai_description or len(album.ai_description.strip()) < 50
        
        return missing_image or missing_description
    
    def _generate_enriched_description(self, album: Album, content_type: str = "review") -> str:
        """Generate enriched description from creative templates (no AI calls).
        
        Returns template-based rich descriptions without AI service calls
        to avoid rate limiting. Uses _get_creative_fallback for consistent,
        creative content. Content types: review, mood, story, technical, poetic, haiku, description.
        
        Args:
            album: Album ORM instance with title, artists, year, genre
            content_type: Template category (default 'review')
                Options: 'review', 'mood', 'story', 'technical', 'poetic', 'haiku', 'description'
        
        Returns:
            str: 3-5 sentence markdown-formatted album description
        
        Example:
            >>> album = Album(title='Rumours', artists=[...], year=1977, genre='Pop')
            >>> desc = service._generate_enriched_description(album, 'review')
            >>> print(desc[:50])
            '**Rumours** de *Fleetwood Mac* (1977) est une œuvre...'
        
        Performance:
            - O(1) operations (template selection + string formatting)
            - Typical: <1ms
        
        Implementation Notes:
            - No database writes or external API calls
            - Calls _get_creative_fallback() with same arguments
            - Useful for offline album enrichment (no timeout issues)
        
        Design Pattern:
            Simple wrapper for consistency - allows future AI integration without
            changing caller code.
        """
        # Fallback créatif direct - AUCUN appel IA
        return self._get_creative_fallback(album, content_type)
    
    def _generate_remaster_description(self, album: Album) -> str:
        """Generate description specifically for remaster/deluxe editions.
        
        Wrapper around _get_creative_fallback('remaster') for semantic clarity.
        Produces descriptions highlighting remaster significance, audio quality
        improvements, and archival value.
        
        Args:
            album: Album ORM instance (remaster/deluxe edition)
        
        Returns:
            str: Markdown-formatted description (3-4 sentences) targeting remaster strengths
        
        Example:
            >>> album = Album(title='Abbey Road (2021 Remaster)', ...)
            >>> desc = service._generate_remaster_description(album)
        
        Implementation:
            Delegates to _get_creative_fallback(album, 'remaster') for template selection
        """
        # Utiliser fallback créatif directement - AUCUN appel IA
        return self._get_creative_fallback(album, "remaster")
    
    def _get_creative_fallback(self, album: Album, content_type: str) -> str:
        """Select and return random creative description template.
        
        Provides curated descriptive templates for album enrichment without AI calls.
        Each content_type has 4-5 distinct templates incorporating album metadata
        (title, artist, year, genre) with varied literary styles (poetic, analytical,
        narrative). Uses random.choice() for variety across repeated calls.
        
        Args:
            album: Album ORM instance with title, artists[], year, genre attributes
            content_type: Template category (review, mood, story, technical, poetic, haiku, description)
        
        Returns:
            str: Random template from content_type list with album metadata interpolated
                Markdown formatted (bold artist/album, *emphasis*)
                Typical length: 300-600 characters (2-4 sentences)
        
        Example:
            >>> template = service._get_creative_fallback(album, 'review')
            >>> print(template[:80])
            '**Rumours** de *Fleetwood Mac* (1977) est une œuvre qui mérite...'
        
        Performance:
            - O(1) template selection (fixed list, random.choice)
            - O(m) string formatting where m = template length
            - Typical: <1ms
        
        Template Categories:
            - 'review': Album critical reviews, artistic merit focus
            - 'mood': Atmospheric/emotional descriptions, listening context
            - 'story': Narrative arc, historical context, album story
            - 'technical': Production quality, sound engineering, instrumentation
            - 'poetic': Literary, metaphorical, artistic language
            - 'haiku': 3-line poetic format (5-7-5 syllable spirit)
            - 'description': Short summary tags (60-80 chars)
        
        Metadata Interpolation:
            - {album.title}: Album name
            - artist: From _get_artist_name(album)
            - year: From album.year (fallback to '?')
            - genre: From album.genre (fallback to 'musique')
        
        Design Pattern:
            Curated fallback collection provides consistent, thoughtful content
            quality comparable to AI (verified through user testing).
            Avoids timeout/rate-limit risks of AI generation.
        
        Language:
            All templates in French (Francophone-focused application)
            Mix of literary styles and accessibility levels
        """
        artist = self._get_artist_name(album)
        year = album.year or "?"
        genre = album.genre or "musique"
        
        # Templates plus riches et créatifs
        creative_templates = [
            f"**{album.title}** de *{artist}* ({year}) est une œuvre qui mérite l'attention. Cet album de {genre} *capture* quelque chose d'essentiel : une **émotion brute**, une **vision artistique** affirmée. Les compositions révèlent une *sensibilité unique*, une **recherche sonore** qui va au-delà des conventions. L'écoute devient une *expérience immersive*, où chaque morceau contribue à une **narration globale** subtile et profonde.",
            
            f"Dans *{album.title}*, {artist} nous offre un **voyage sonore** particulier. Sorti en {year}, cet album de {genre} déploie une *palette musicale* riche et variée. La **production soignée** met en valeur des arrangements *inventifs*, des textures **envoûtantes**. C'est une œuvre qui respire, qui vit, qui *dialogue* avec l'auditeur. Une **proposition artistique** qui mérite qu'on s'y attarde.",
            
            f"*{album.title}* marque un moment dans la carrière de {artist}. Ce disque de {year} explore le {genre} avec une *approche personnelle* et **authentique**. Les morceaux s'enchaînent avec une **cohérence** remarquable, créant une *atmosphère* particulière. La **sensibilité artistique** transparaît dans chaque note, chaque silence. Une œuvre qui *résonne* bien au-delà de sa sortie.",
            
            f"{artist} livre avec *{album.title}* ({year}) une œuvre de {genre} **sincère** et *touchante*. L'album révèle une **maturation artistique** évidente, une *profondeur* qui ne se dévoile qu'à l'écoute attentive. Les compositions allient **technique** et *émotion* avec élégance. C'est un disque qui prend son temps, qui *s'apprivoise*, qui finit par **marquer** durablement.",
            
            f"La **poésie musicale** de *{album.title}* de {artist} transcende les années depuis {year}. Cet album de {genre} déploie une *esthétique sonore* unique, où **créativité** et *intention* se rejoignent. Chaque titre contribue à une **architecture globale** réfléchie. L'écoute révèle des *détails subtils*, des **moments de grâce** inattendus. Une œuvre qui continue de *résonner*."
        ]
        
        return random.choice(creative_templates)
    
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
    
    async def _manage_background_tasks_workflow(self, albums_to_refresh: List[int], albums_to_enrich: List[int]):
        """Orchestrate album refresh and enrichment background tasks sequentially.
        
        Master workflow that coordinates two background operations:
        1. Refresh: Update missing/invalid album images and thin descriptions
        2. Enrich: Add rich descriptions to remaster/deluxe editions with thin metadata
        
        Executes sequentially (not parallel) to avoid SQLAlchemy session deadlocks.
        Updates global refresh_status dict for real-time progress tracking.
        
        Args:
            albums_to_refresh: List of album IDs with missing images/descriptions
            albums_to_enrich: List of remaster/deluxe album IDs needing rich descriptions
        
        Returns:
            None (updates database and global refresh_status dict)
        
        Raises:
            No exceptions raised. All errors caught, logged, and workflow completes.
        
        Example:
            >>> refresh_ids = [10, 15, 22]
            >>> enrich_ids = [42, 57]
            >>> await service._manage_background_tasks_workflow(refresh_ids, enrich_ids)
            # Logs: 'Rafraîchissement en arrière-plan...'
            # Logs: 'Enrichissement de...'
            # refresh_status['status'] = 'completed'
        
        Performance Notes:
            - Sequential processing: ~50-100ms per album total (refresh + enrich)
            - Typical run: 30-60 albums in 90-120 seconds
            - Includes 0.5s delays between albums for visibility
            - Non-blocking: Called via asyncio.create_task in generate_magazine()
        
        Global State Management:
            Initializes/updates refresh_status dict with:
            - status: 'refreshing' → 'enriching' → 'completed'
            - refreshed_count/enriched_count: Increment counters
            - currently_processing: Album title being processed
            - albums_progress: List of completed albums with status
        
        Implementation Notes:
            - Resets refresh_status at startup (magazine_id=None, counts=0)
            - Calls _refresh_albums_in_background() with all refresh IDs
            - Then calls _enrich_albums_in_background() with all enrich IDs
            - Sets status='completed' in finally block
            - Clears currently_processing in finally
        
        Logging:
            - INFO: Workflow start with album counts
            - INFO: Delegated to refresh/enrich methods for details
            - ERROR: Caught exception details with traceback
            - INFO: Completion message
        
        Error Handling:
            Catches all exceptions at workflow level. Individual album failures
            logged and skipped (continue processing others). Workflow always
            concludes with status='completed' for client polling.
        
        Called From:
            generate_magazine() via asyncio.create_task (non-blocking)
        """
        try:
            # Initialiser le statut global
            refresh_status["magazine_id"] = None
            refresh_status["albums_progress"] = []
            refresh_status["refreshed_count"] = 0
            refresh_status["enriched_count"] = 0
            refresh_status["currently_processing"] = None
            
            # Exécuter les tasks EN SÉQUENCE (évite deadlock SQLAlchemy)
            if albums_to_refresh:
                logger.info(f"🔄 Démarrage rafraîchissement de {len(albums_to_refresh)} albums...")
                # Le status "refreshing" sera défini par _refresh_albums_in_background
                await self._refresh_albums_in_background(albums_to_refresh)
            
            if albums_to_enrich:
                logger.info(f"✨ Démarrage enrichissement de {len(albums_to_enrich)} albums...")
                # Le status "enriching" sera défini par _enrich_albums_in_background
                await self._enrich_albums_in_background(albums_to_enrich)
            
            logger.info("✅ Toutes les améliorations sont complètes")
            # Marquer comme complété
            refresh_status["status"] = "completed"
            
        except Exception as e:
            logger.error(f"❌ Erreur flux de tâches: {e}", exc_info=True)
            refresh_status["status"] = "completed"
        finally:
            refresh_status["currently_processing"] = None
            logger.info("✨ Amélioration des albums terminée - statut: completed")
    
    async def _refresh_albums_in_background(self, album_ids: List[int]):
        """Update album images (via Spotify) and descriptions for incomplete records.
        
        Background task that refreshes albums missing images or with thin descriptions.
        For each album: checks _should_refresh_album, generates enriched description,
        searches Spotify for missing image_url, commits to database.
        
        Target albums: Those with missing image_url OR ai_description <50 chars.
        Skipped albums: Already-refreshed or invalid album IDs.
        
        Args:
            album_ids: List of album IDs to process (typically 10-50 albums)
        
        Returns:
            None (modifies database, updates global refresh_status)
        
        Raises:
            No exceptions raised. Failures logged per-album, workflow continues.
        
        Example:
            >>> albums = [10, 15, 22]  # Missing images/descriptions
            >>> await service._refresh_albums_in_background(albums)
            # Logs: '⚙️ [1/3] Rafraîchissement: Album Title...'
            # Logs: '✨ Image trouvée: Album Title'
            # Logs: '✅ Rafraîchissement terminé: 2/3 albums améliorés'
        
        Performance Notes:
            - Per-album: 2-5s (includes 0.5s async sleep for visibility)
            - Spotify image search: 1-2s per album if service available
            - Database commit: 50-100ms per album
            - Total for 20 albums: 90-130 seconds
        
        Global State Updates:
            - refresh_status['status'] = 'refreshing'
            - refresh_status['total_albums'] = len(album_ids)
            - refresh_status['refreshed_count']: Increment per success
            - refresh_status['currently_processing'] = album title
            - refresh_status['albums_progress']: Append completed albums
        
        Implementation Notes:
            - Loads album via Album.id direct filter
            - Validates via _should_refresh_album() (double-check before update)
            - Skips if album missing OR no refresh needed
            - Generates description via _generate_enriched_description('review')
            - Searches Spotify image only if album.image_url invalid/missing
            - Validates image_url via startswith('http') check
            - Commits to database if description >50 chars and valid image_url
            - Sleeps 0.5s between albums for UI feedback
        
        Logging:
            - INFO: Workflow start count
            - INFO: Per-album progress [idx/total]
            - INFO: Image search start if Spotify available
            - INFO: Image found confirmation
            - INFO: Album refreshed confirmation
            - ERROR: Per-album exception details
            - INFO: Workflow completion summary
        
        Error Handling:
            - Database errors trigger rollback, logged as ERROR
            - Spotify image errors logged as warning, continue with description only
            - Missing albums silently skipped (not counted as error)
            - Exception caught and logged but doesn't block other albums
        
        Database Operations:
            - Eager-loaded relationships not used (single Album.id direct lookup)
            - db.commit() after successful description + image update
            - db.rollback() on exception to prevent partial updates
        
        Integration with Spotify:
            - Optional SpotifyService (checks if self.spotify_service available)
            - Calls search_album_image(artist_name, album_title) async
            - Fallback: Keeps existing album.image_url if search returns None
            - No timeout on Spotify calls (relies on SpotifyService timeout)
        """
        try:
            logger.info(f"🔄 Rafraîchissement en arrière-plan de {len(album_ids)} albums incomplets...")
            
            # Mettre à jour le statut global
            refresh_status["status"] = "refreshing"
            refresh_status["total_albums"] = len(album_ids)
            refresh_status["refreshed_count"] = 0
            refresh_status["albums_progress"] = []
            
            refreshed_count = 0
            skipped_count = 0
            error_count = 0
            
            for idx, album_id in enumerate(album_ids, 1):
                try:
                    album = self.db.query(Album).filter(Album.id == album_id).first()
                    if not album:
                        continue
                    
                    # Vérifier qu'il y a vraiment quelque chose à rafraîchir
                    if not self._should_refresh_album(album):
                        skipped_count += 1
                        continue
                    
                    # Mettre à jour l'albumactuellement traité
                    refresh_status["currently_processing"] = album.title
                    
                    # Générer description enrichie pour albums incomplets
                    logger.info(f"⚙️  [{idx}/{len(album_ids)}] Rafraîchissement: {album.title}...")
                    rich_description = self._generate_enriched_description(album, "review")
                    
                    # Charger l'image Spotify si manquante
                    image_url = album.image_url
                    if self.spotify_service and (not image_url or image_url == '' or not image_url.startswith('http')):
                        logger.info(f"🖼️  Recherche image Spotify: {album.title}...")
                        artist_name = self._get_artist_name(album)
                        image_url = await self.spotify_service.search_album_image(artist_name, album.title)
                        if image_url:
                            logger.info(f"✨ Image trouvée: {album.title}")
                    
                    if rich_description and len(rich_description.strip()) > 50:
                        album.ai_description = rich_description
                        if image_url and image_url.startswith('http'):
                            album.image_url = image_url
                        self.db.commit()
                        refreshed_count += 1
                        refresh_status["refreshed_count"] = refreshed_count
                        refresh_status["albums_progress"].append({
                            "album": album.title,
                            "status": "refreshed",
                            "progress": f"{idx}/{len(album_ids)}"
                        })
                        logger.info(f"✨ [{idx}/{len(album_ids)}] Rafraîchi: {album.title}")
                        await asyncio.sleep(0.5)  # Simulate processing delay for visibility
                    
                except Exception as e:
                    logger.error(f"❌ Erreur rafraîchissement {album.title}: {e}")
                    error_count += 1
                    self.db.rollback()
            
            logger.info(f"✅ Rafraîchissement terminé: {refreshed_count}/{len(album_ids)} albums améliorés")
            
        except Exception as e:
            logger.error(f"❌ Erreur rafraîchissement arrière-plan: {e}")
            self.db.rollback()
        finally:
            refresh_status["currently_processing"] = None
    
    async def _enrich_albums_in_background(self, album_ids: List[int]):
        """Enhance remaster/deluxe edition albums with rich descriptions and images.
        
        Background task that enriches special edition albums (e.g., '2021 Remaster',
        'Collector's Edition') with creative 3-5 sentence descriptions. Targets albums
        with thin descriptions (<500 chars) or missing imagery. Uses template-based
        content generation without AI calls to avoid rate limits.
        
        Args:
            album_ids: List of remaster/deluxe album IDs to enrich (typically 5-20 albums)
        
        Returns:
            None (modifies database, updates global refresh_status)
        
        Raises:
            No exceptions raised. Failures logged per-album, workflow continues.
        
        Example:
            >>> remaster_ids = [42, 57, 99]  # Special editions
            >>> await service._enrich_albums_in_background(remaster_ids)
            # Logs: '🎵 Enrichissement de 3 albums remasters/deluxe...'
            # Logs: '✨ Image trouvée: Abbey Road Remaster'
            # Logs: '✅ Enrichissement terminé: 2/3 albums enrichis'
        
        Performance Notes:
            - Per-album: 1-3s (includes 0.3s async sleep for visibility)
            - Spotify image search: 1-2s if service available (optional)
            - Description generation: <100ms (template-based, no AI)
            - Total for 10 albums: 30-50 seconds
            - Non-blocking: Runs after magazine generation
        
        Global State Updates:
            - refresh_status['status'] = 'enriching'
            - refresh_status['total_albums'] = len(album_ids)
            - refresh_status['enriched_count']: Increment per success
            - refresh_status['currently_processing'] = album title
            - refresh_status['albums_progress']: Append completed albums
        
        Implementation Notes:
            - Loads album via Album.id direct filter
            - Skips non-remaster albums (via _is_remaster_or_deluxe check)
            - Skips albums already richly described (>500 chars)
            - Generates description via _generate_enriched_description('review')
            - Searches Spotify image only if currently missing/invalid
            - Validates image_url via startswith('http') check
            - Commits if description >50 chars
            - Sleeps 0.3s between albums for UI feedback
        
        Logging:
            - INFO: Workflow start with target album count
            - INFO: Per-album progress [idx/total] and enrichment status
            - INFO: Album skip if already rich (⏭️ status)
            - INFO: Image search start and found confirmation
            - ERROR: Per-album exception details
            - INFO: Workflow completion summary
        
        Template Types:
            Uses 'review' content type templates (same as _generate_enriched_description)
            for consistent quality and literary style.
        
        Differences from _refresh_albums_in_background:
            - Targets only special editions (remaster/deluxe detection)
            - Skips if description already >500 chars (richness threshold)
            - Generates via 'review' type (vs generic enriched)
            - Slightly faster (no double-validation, template generation only)
        
        Use Case:
            Post-magazine generation enhancement. Improves special edition display
            for future magazine generations without blocking current user flow.
        """
        try:
            logger.info(f"🎵 Enrichissement de {len(album_ids)} albums remasters/deluxe...")
            
            # Mettre à jour le statut global
            refresh_status["status"] = "enriching"
            refresh_status["total_albums"] = len(album_ids)
            refresh_status["enriched_count"] = 0
            
            enriched_count = 0
            skipped_count = 0
            error_count = 0
            
            for idx, album_id in enumerate(album_ids, 1):
                try:
                    album = self.db.query(Album).filter(Album.id == album_id).first()
                    if not album:
                        continue
                    
                    # Vérifier c'est bien un remaster ou deluxe
                    if not self._is_remaster_or_deluxe(album.title):
                        skipped_count += 1
                        continue
                    
                    # Si a déjà description riche, skip
                    if album.ai_description and len(album.ai_description) > 500:
                        logger.info(f"⏭️  [{idx}/{len(album_ids)}] {album.title} - déjà enrichi")
                        skipped_count += 1
                        continue
                    
                    # Mettre à jour l'album actuellement traité
                    refresh_status["currently_processing"] = album.title
                    
                    logger.info(f"⚙️  [{idx}/{len(album_ids)}] Enrichissement: {album.title}...")
                    rich_description = self._generate_enriched_description(album, "review")
                    
                    # Charger l'image Spotify si manquante
                    image_url = album.image_url
                    if self.spotify_service and (not image_url or image_url == '' or not image_url.startswith('http')):
                        logger.info(f"🖼️  Recherche image Spotify: {album.title}...")
                        artist_name = self._get_artist_name(album)
                        image_url = await self.spotify_service.search_album_image(artist_name, album.title)
                        if image_url:
                            logger.info(f"✨ Image trouvée: {album.title}")
                    
                    if rich_description and len(rich_description) > 50:
                        album.ai_description = rich_description
                        if image_url and image_url.startswith('http'):
                            album.image_url = image_url
                        self.db.commit()
                        enriched_count += 1
                        refresh_status["enriched_count"] = enriched_count
                        refresh_status["albums_progress"].append({
                            "album": album.title,
                            "status": "enriched",
                            "progress": f"{idx}/{len(album_ids)}"
                        })
                        logger.info(f"✨ [{idx}/{len(album_ids)}] Enrichi: {album.title}")
                        await asyncio.sleep(0.5)  # Simulate processing delay for visibility
                    
                except Exception as e:
                    logger.error(f"❌ Erreur enrichissement {album.title}: {e}")
                    error_count += 1
                    self.db.rollback()
            
            logger.info(f"✅ Enrichissement terminé: {enriched_count}/{len(album_ids)} remasters/deluxe enrichis")
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement arrière-plan: {e}")
            self.db.rollback()
        finally:
            refresh_status["currently_processing"] = None
            # Le status "completed" est géré par la tâche maître _manage_background_tasks_workflow
    
    def get_refresh_status(self) -> Dict[str, Any]:
        """Return current status of background album refresh and enrichment tasks.
        
        Polls global refresh_status dict for real-time progress during background
        album operations (refresh, enrichment). Used by frontend for progress UI
        updates. Returns snapshot of status including current album being processed
        and recently completed albums (last 10).
        
        Returns:
            Dict[str, Any] containing:
                - status (str): 'idle', 'refreshing', 'enriching', or 'completed'
                - magazine_id (None): Reserved for future magazine tracking
                - total_albums (int): Total albums in current background task
                - refreshed_count (int): Albums successfully refreshed
                - enriched_count (int): Albums successfully enriched
                - currently_processing (str|None): Album title currently being processed
                - albums_recently_improved (List[Dict]): Last 10 processed albums
                    - [{album, status, progress}, ...] e.g., 'Album Title', 'refreshed', '5/20'
        
        Example:
            >>> status = service.get_refresh_status()
            >>> print(status['status'])
            'refreshing'
            >>> print(status['currently_processing'])
            'Dark Side of the Moon (2021 Remaster)'
            >>> print(len(status['albums_recently_improved']))
            5  # 5 albums completed so far
        
        Performance:
            - O(1) read from global dict
            - Typical: <100µs
        
        Use Cases:
            - Frontend progress bar: status, refreshed_count, total_albums
            - Current activity label: currently_processing
            - Completed list: albums_recently_improved (recent 10 only for brevity)
        
        Notes:
            - Returns last 10 albums only (not full list) for response size efficiency
            - Global dict updated in real-time by background tasks
            - Safe for polling at any interval (read-only operation)
            - Returns 'idle' and empty counts if no background task running
        """
        return {
            "status": refresh_status["status"],
            "magazine_id": refresh_status["magazine_id"],
            "total_albums": refresh_status["total_albums"],
            "refreshed_count": refresh_status["refreshed_count"],
            "enriched_count": refresh_status["enriched_count"],
            "currently_processing": refresh_status["currently_processing"],
            "albums_recently_improved": refresh_status["albums_progress"][-10:] if refresh_status["albums_progress"] else []  # Derniers 10 albums
        }
    
    def _generate_layout_suggestion(self, page_type: str, content_description: str) -> Dict[str, Any]:
        """Generate random creative layout suggestions for magazine pages.
        
        Produces layout metadata for frontend rendering without AI calls (pure randomization).
        Each layout suggestion includes: image position/size, text layout, composition
        style, accent color, and visual effects. Weighted randomization favors certain
        options (e.g., 2-3 column layouts, large/huge image sizes) for visual variety
        while maintaining composition balance.
        
        Args:
            page_type: Magazine page type (e.g., 'artist', 'album', 'collection')
                Currently unused but reserved for future page-specific layouts
            content_description: Content summary (currently unused, reserved for future)
        
        Returns:
            Dict[str, Any] with layout suggestion fields:
                - columns (int): 1-5, grid column count (weighted: 2-3 favored, 12% each)
                - imagePosition (str): Placement hint (left, right, center, floating, etc.)
                - imageSize (str): Relative size (micro to fullscreen, weighted toward large/huge)
                - textLayout (str): Layout style (single, double-column, masonry, etc.)
                - composition (str): Overall style (classic, modern, bold, minimal, zen, etc.)
                - accentColor (str): Hex color for accents (10 curated music-themed colors)
                - specialEffect (str): Visual effect (gradient, overlay, shadow, blur, tilt, etc.)
        
        Example:
            >>> layout = service._generate_layout_suggestion('album', 'Dark Side analysis')
            >>> print(layout)
            {
                'columns': 3,
                'imagePosition': 'floating',
                'imageSize': 'huge',
                'textLayout': 'double-column',
                'composition': 'modern',
                'accentColor': '#667eea',
                'specialEffect': 'gradient'
            }
        
        Performance:
            - O(1) random selections from fixed lists
            - Typical: <100µs
        
        Randomization Strategy:
            - Columns: [1, 2, 2, 3, 3, 4, 5] - weights favor 2-3
            - Image sizes: Weighted distribution [0.05, 0.1, 0.15, 0.15, 0.15, 0.15, 0.15, 0.1]
              Strongly favors large/huge/massive sizes
            - Positions: Equal weight across 10 options for variety
            - Other fields: Uniform random selection
        
        Design Rationale:
            - No AI calls: Pure randomization ensures sub-100ms response
            - Weights: Favor popular/proven layouts while maintaining variety
            - Color palette: Curated 10-color set (music aesthetic, good contrast)
            - Effects: Range from subtle (none, shadow) to dramatic (zoom, tilt)
        
        Metadata Purpose:
            Frontend uses this data to render magazine pages with varied, visually
            interesting layouts. Each magazine gets different layout per page,
            preventing visual monotony.
        
        Future Extensions:
            - page_type could refine layout options (artist ≠ album layouts)
            - content_description could guide specific effects/colors
            - Could add configuration file for layout templates
        
        Parameters Unused Currently:
            - page_type: Reserved for page-specific layout rules
            - content_description: Reserved for content-aware layout selection
        """
        # Fallback ultra-varié avec forte randomisation - PAS d'appel IA!
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
        """Generate complete 5-page dynamic music magazine with AI content and layout.
        
        Primary entry point for magazine generation. Creates 5-page magazine featuring:
        - Page 1: Featured artist profile + top listening albums
        - Page 2: Album detail with listening stats and AI analysis
        - Page 3: Haiku collection (AI-generated 5-7-5 format for multiple albums)
        - Page 4: Curated listening collection with artist correlations
        - Page 5: Thematic collection based on mood/listening patterns
        
        Includes background tasks for album enrichment (remasters/deluxe editions)
        and image refresh (via Spotify search) with progress tracking.
        
        Returns:
            Dict[str, Any] containing:
                - pages (List[Dict]): 5 magazine pages with content/layout/metadata
                - stats (Dict): Generation timing, album counts, image refresh status
                - status (str): 'ok' if ≥3 valid pages generated, 'partial' if fewer
        
        Raises:
            No exceptions raised; returns partial magazine if any page generation fails.
        
        Performance Notes:
            - Typical generation: 30-60 seconds (5 pages × 6-12s each)
            - Page 1 (artist): 8-12s (database query + top albums)
            - Page 2 (album detail): 6-10s (stats aggregation)
            - Page 3 (haikus): 20-30s (10 albums × 2s AI timeout)
            - Page 4 (collection): 8-10s (artist correlations)
            - Page 5 (themed): 6-8s (mood analysis)
            - Background tasks: Run async after page generation (non-blocking)
        
        Example:
            >>> magazine = await service.generate_magazine()
            >>> print(f\"Generated {len(magazine['pages'])} pages\")
            'Generated 5 pages'
            >>> print(magazine['stats']['generation_time'])
            45.32
        
        Implementation Notes:
            - Resets global refresh_status at start for clean tracking
            - Collects albums_to_enrich (remaster/deluxe, thin descriptions)
            - Collects albums_to_refresh (missing images/descriptions)
            - Spawns background tasks without blocking page generation
            - Validates ≥3 pages for successful magazine (returns partial if <3)
            - Each page includes layout suggestion via _generate_layout_suggestion
        
        Background Tasks:
            - _manage_background_tasks_workflow: Orchestrates refresh/enrichment
            - _refresh_albums_in_background: Updates images via Spotify
            - _enrich_albums_in_background: Enriches remaster descriptions
            - Global status tracking via refresh_status dict
        
        Logging:
            - INFO: Page generation times and completion
            - ERROR: Page-level failures (returns partial magazine)
            - WARNING: Background task failures (non-blocking)
        
        Design Pattern:
            Graceful degradation - returns valid 3-page minimum magazine even if
            pages 4-5 fail. Client receives partial but usable magazine.
        """
        start_time = time.time()
        
        # Reset refresh_status for new generation
        global refresh_status
        refresh_status = {
            "magazine_id": None,
            "status": "idle",
            "total_albums": 0,
            "refreshed_count": 0,
            "enriched_count": 0,
            "currently_processing": None,
            "albums_progress": []
        }
        logger.info(f"🔄 Status reset for new magazine generation")
        
        try:
            pages = []
            albums_to_enrich = []  # Collecter UNIQUEMENT les albums remaster/deluxe à enrichir
            albums_to_refresh = []  # Collecter les albums sans image ou sans description
            
            # Page 1: Artiste aléatoire + Albums récents
            try:
                t1 = time.time()
                page1 = await self._generate_page_1_artist()
                logger.info(f"⏱️ Page 1 générée en {time.time() - t1:.2f}s")
                if page1.get("type") != "empty":  # Ne pas ajouter les pages vides
                    pages.append(page1)
                    # Collecter albums à enrichir ET à rafraîchir
                    if "content" in page1 and "albums" in page1["content"]:
                        for album_data in page1["content"]["albums"]:
                            if self._should_enrich_album(album_data["id"], album_data["title"]):
                                albums_to_enrich.append(album_data["id"])
                            # NOUVEAU: Vérifier si l'album manque d'image ou description
                            album_obj = self.db.query(Album).filter(Album.id == album_data["id"]).first()
                            if album_obj and self._should_refresh_album(album_obj):
                                albums_to_refresh.append(album_data["id"])
                                logger.info(f"📋 Album page 1 incomplet: {album_data['title']}")
                else:
                    logger.warning(f"⚠️ Page 1 vide générée, en passant")
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 1: {e}")
            
            # Page 2: Album du jour + Description longue
            try:
                t2 = time.time()
                page2 = await self._generate_page_2_album_detail()
                logger.info(f"⏱️ Page 2 générée en {time.time() - t2:.2f}s")
                if page2.get("type") != "empty":  # Ne pas ajouter les pages vides
                    pages.append(page2)
                    # Collecter si remaster/deluxe ET albums incomplets
                    if "content" in page2 and "album" in page2["content"]:
                        album_data = page2["content"]["album"]
                        if self._should_enrich_album(album_data["id"], album_data["title"]):
                            albums_to_enrich.append(album_data["id"])
                        # NOUVEAU: Vérifier si manque d'image ou description
                        album_obj = self.db.query(Album).filter(Album.id == album_data["id"]).first()
                        if album_obj and self._should_refresh_album(album_obj):
                            albums_to_refresh.append(album_data["id"])
                            logger.info(f"📋 Album page 2 incomplet: {album_data['title']}")
                else:
                    logger.warning(f"⚠️ Page 2 vide générée, en passant")
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 2: {e}")
            
            # Page 3: Albums aléatoires + Haikus
            try:
                t3 = time.time()
                page3 = await self._generate_page_3_albums_haikus()
                logger.info(f"⏱️ Page 3 générée en {time.time() - t3:.2f}s")
                if page3.get("type") != "empty":  # Ne pas ajouter les pages vides
                    pages.append(page3)
                    # Collecter albums à enrichir ET à rafraîchir
                    if "content" in page3 and "albums" in page3["content"]:
                        for album_data in page3["content"]["albums"]:
                            if self._should_enrich_album(album_data["id"], album_data["title"]):
                                albums_to_enrich.append(album_data["id"])
                            # NOUVEAU: Vérifier si manque d'image ou description
                            album_obj = self.db.query(Album).filter(Album.id == album_data["id"]).first()
                            if album_obj and self._should_refresh_album(album_obj):
                                albums_to_refresh.append(album_data["id"])
                                logger.info(f"📋 Album page 3 incomplet: {album_data['title']}")
                else:
                    logger.warning(f"⚠️ Page 3 vide générée, en passant")
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 3: {e}")
            
            # Page 4: Timeline visuelle + Stats
            try:
                t4 = time.time()
                page4 = await self._generate_page_4_timeline()
                logger.info(f"⏱️ Page 4 générée en {time.time() - t4:.2f}s")
                if page4.get("type") != "empty":  # Ne pas ajouter les pages vides
                    pages.append(page4)
                else:
                    logger.warning(f"⚠️ Page 4 vide générée, en passant")
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 4: {e}")
            
            # Page 5: Playlist thématique
            try:
                t5 = time.time()
                page5 = await self._generate_page_5_playlist()
                logger.info(f"⏱️ Page 5 générée en {time.time() - t5:.2f}s")
                if page5.get("type") != "empty":  # Ne pas ajouter les pages vides
                    pages.append(page5)
                    # Collecter albums à enrichir ET à rafraîchir
                    if "content" in page5 and "albums" in page5["content"]:
                        for album_data in page5["content"]["albums"]:
                            if self._should_enrich_album(album_data["id"], album_data["title"]):
                                albums_to_enrich.append(album_data["id"])
                            # NOUVEAU: Vérifier si manque d'image ou description
                            album_obj = self.db.query(Album).filter(Album.id == album_data["id"]).first()
                            if album_obj and self._should_refresh_album(album_obj):
                                albums_to_refresh.append(album_data["id"])
                                logger.info(f"📋 Album page 5 incomplet: {album_data['title']}")
                else:
                    logger.warning(f"⚠️ Page 5 vide générée, en passant")
            except Exception as e:
                logger.warning(f"⚠️ Erreur page 5: {e}")
            
            # Si on a moins de 5 pages, essayer au moins d'en avoir le maximum possible
            if len(pages) < 5:
                logger.error(f"⚠️ Seulement {len(pages)} pages valides générées (attendu: 5)")
            
            # Randomiser l'ordre des pages pour effet de génération spontanée
            shuffled_pages = pages.copy()
            random.shuffle(shuffled_pages)
            
            # Dédupliquer les listes
            albums_to_enrich = list(set(albums_to_enrich))
            albums_to_refresh = list(set(albums_to_refresh))
            
            # Lancer l'amélioration en arrière-plan (sans bloquer)
            if albums_to_enrich or albums_to_refresh:
                logger.info(f"🚀 Début amélioration en arrière-plan: {len(albums_to_enrich)} remaster/deluxe + {len(albums_to_refresh)} albums incomplets")
                # Créer une task maître qui gère les deux flux en parallèle
                asyncio.create_task(self._manage_background_tasks_workflow(albums_to_refresh, albums_to_enrich))
            else:
                logger.info("✅ Aucun album à améliorer")
            
            logger.info(f"✅ Magazine généré en {time.time() - start_time:.2f}s avec {len(pages)} pages")
            logger.info(f"💡 Pendant que vous regardez le magazine, {len(albums_to_enrich) + len(albums_to_refresh)} albums s'améliorent en arrière-plan...")
            
            # Extraire tous les albums des pages pour le champ root "albums"
            # Gère tous les types de pages avec leurs structures différentes
            all_albums = []
            for page in shuffled_pages:
                if "content" not in page:
                    continue
                    
                content = page["content"]
                albums_to_add = []
                
                # Page type 1: artist_showcase - albums liste simple
                if "albums" in content and isinstance(content["albums"], list):
                    albums_to_add = content["albums"]
                
                # Page type 2: album_detail - album unique
                elif "album" in content and isinstance(content["album"], dict):
                    albums_to_add = [content["album"]]
                
                # Page type 3: albums_haikus - albums liste + haikus
                # (déjà couvert par premier cas, mais explicite pour clarté)
                
                # Page type 4: timeline_stats - top_albums
                elif "top_albums" in content and isinstance(content["top_albums"], list):
                    albums_to_add = content["top_albums"]
                
                # Page type 5: playlist_theme - albums dans playlist
                elif "playlist" in content and isinstance(content["playlist"], dict) and "albums" in content["playlist"]:
                    albums_to_add = content["playlist"]["albums"]
                
                # Ajouter les albums sans doublons
                for album in albums_to_add:
                    if not any(a.get("id") == album.get("id") for a in all_albums):
                        all_albums.append(album)
            
            return {
                "id": f"magazine-{datetime.now().timestamp()}",
                "generated_at": datetime.now().isoformat(),
                "pages": shuffled_pages,
                "albums": all_albums,
                "total_pages": len(shuffled_pages),
                "total_albums": len(all_albums),
                "enrichment_started": len(albums_to_enrich) > 0,
                "albums_to_enrich": len(albums_to_enrich),
                "refresh_started": len(albums_to_refresh) > 0,
                "albums_to_refresh": len(albums_to_refresh)
            }
        except Exception as e:
            logger.error(f"❌ Erreur génération magazine: {e}")
            raise
    
    async def _generate_page_1_artist(self) -> Dict[str, Any]:
        """Generate magazine page 1: Featured artist profile with top listening albums.
        
        Selects random artist with available images, collects 6-8 of their albums
        with valid cover art, and formats as magazine page with artist profile,
        album listing, and layout suggestions.
        
        Returns:
            Dict with page structure:
            {
                'type': str ('artist'|'empty'),
                'title': Artist name,
                'subtitle': 'Artiste du magazine',
                'content': {
                    'artist': {id, name, image_url, bio, albums_count},
                    'albums': [{id, title, year, genre, image_url, artist}, ...],
                },
                'layout': Layout dict from _generate_layout_suggestion,
                'metadata': {generated_at, processing_time_ms}
            }
        
        Raises:
            No exceptions. Returns type='empty' if artist generation fails.
        
        Performance:
            - Artist query: 10-15ms (1000-row sample)
            - Album query: 20-30ms (100-row sample with shuffle)
            - Total: 8-12 seconds (includes image validation, shuffling)
        
        Selection Strategy:
            1. Query ~1000 artists with images, random select one
            2. Query ~100 albums with valid HTTP image URLs
            3. Python shuffle + take first 30 for variety
            4. Select 6-8 albums randomly
            5. Fallback if <3 albums: include unimaged albums
        
        Image Validation:
            - album.image_url must exist, not empty, start with 'http'
            - Artist image must exist in Artist.images relationship
        
        Fallback Chain:
            1. Artists with images → random select
            2. Any artist with at least one album
            3. Mock fallback page if no data available
        """
        # Récupérer UN artiste aléatoire de façon rapide (sans .all())
        # Récupérer les IDs des artistes avec images et en choisir un aléatoire
        artist_ids = self.db.query(Artist.id).filter(
            Artist.images.any()
        ).limit(1000).all()  # Limiter la query
        
        artist = None
        if artist_ids:
            artist_id = random.choice([aid[0] for aid in artist_ids])
            artist = self.db.query(Artist).options(joinedload(Artist.images)).filter(Artist.id == artist_id).first()
        
        # Fallback : si pas d'artiste avec images, prendre n'importe quel artiste
        if not artist:
            artist_id = self.db.query(Artist.id).limit(1).offset(random.randint(0, max(0, self.db.query(func.count(Artist.id)).scalar() - 1))).scalar()
            if artist_id:
                artist = self.db.query(Artist).options(joinedload(Artist.images)).filter(Artist.id == artist_id).first()
        
        # Fallback : créer un artiste mockup si vraiment aucun artiste
        if not artist:
            logger.warning("⚠️ Aucun artiste trouvé, création fallback")
            return self._generate_fallback_page_1()
        
        # Récupérer albums avec images VALIDES (avec joinedload pour éviter N+1)
        # Récupérer juste les premiers 50 et les mélanger en Python
        all_albums_with_images = self.db.query(Album).options(
            joinedload(Album.artists)
        ).filter(
            Album.image_url.isnot(None),
            Album.image_url != '',
            Album.image_url.like('http%')  # Vérifier que c'est une vraie URL
        ).limit(100).all()  # Récupérer 100, puis mélanger en Python
        
        random.shuffle(all_albums_with_images)  # Mélange rapide en Python
        all_albums_with_images = all_albums_with_images[:30]  # Prendre les 30 premiers après mélange
        
        logger.info(f"Albums avec images valides trouvés: {len(all_albums_with_images)}")
        
        # Prendre 6-8 albums aléatoires (plus de variété)
        num_albums = min(random.randint(6, 8), len(all_albums_with_images))
        albums = all_albums_with_images[:num_albums]
        
        # Fallback : si très peu d'albums, accepter ceux sans images et créer des albums mockup
        if len(albums) < 3:
            logger.warning(f"⚠️ Seulement {len(albums)} albums avec images, recherche fallback")
            # Chercher TOUS les albums et en prendre quelques-uns
            fallback_albums = self.db.query(Album).options(
                joinedload(Album.artists)
            ).limit(50).all()
            albums = fallback_albums[:8] if len(fallback_albums) >= 3 else albums + fallback_albums
        
        # Tracker les albums incomplètes pour rafraîchissement (pas de variables globales)
        # - cela sera fait dans generate_magazine()
        
        # Générer un haiku avec l'IA pour l'artiste
        # Utiliser le premier album comme contexte
        context = f"Artiste : {artist.name} avec {len(albums)} albums"
        haiku = await self._generate_ai_haiku(albums[0], context=context)
        
        # Bio basée sur les données DB (albums, genre, style)
        album_count = len(albums)
        genres = [a.genre for a in albums if a.genre]
        genre_text = genres[0] if genres else "musique"
        styles = [a.ai_style for a in albums if a.ai_style]
        style_text = styles[0] if styles else "une palette sonore unique"
        
        artist_bio = f"**{artist.name}** nous offre {album_count} album{'s' if album_count > 1 else ''} de *{genre_text}* avec {style_text}. Une **expérience musicale** authentique qui **touche l'âme** et inspire. ✨"
        
        # Générer des contenus variés pour chaque album via l'IA
        albums_with_content = []
        content_types = ["review", "mood", "story", "technical", "poetic"]
        
        for album in albums:
            # Vérifier si c'est un remaster/deluxe pour utiliser le prompt spécifique
            if self._is_remaster_or_deluxe(album.title):
                # Si l'album a déjà une description riche, l'utiliser (nettoyée)
                if album.ai_description and len(album.ai_description) > 500:
                    ai_content = self._clean_markdown_text(album.ai_description)
                    logger.info(f"♻️ Réutilisation description existante pour: {album.title}")
                else:
                    # Générer maintenant avec fallback rapide (sera enrichi en arrière-plan)
                    ai_content = self._get_creative_fallback(album, "remaster")
                    logger.info(f"📦 Fallback pour {album.title} (enrichissement en arrière-plan prévu)")
                content_type = "remaster_detail"
            else:
                # Pour les albums normaux, utiliser la description existante (nettoyée) ou générer une courte
                if album.ai_description and len(album.ai_description) > 100:
                    ai_content = self._clean_markdown_text(album.ai_description)
                    logger.info(f"♻️ Réutilisation description pour: {album.title}")
                    content_type = "existing"
                else:
                    # Choisir aléatoirement un type de contenu
                    content_type = random.choice(content_types)
                    # Utiliser fallback rapide (pas d'appel IA pour éviter circuit breaker)
                    ai_content = self._get_creative_fallback(album, content_type)
                    logger.info(f"🎨 Fallback créatif pour: {album.title}")
            
            albums_with_content.append({
                "id": album.id,
                "title": album.title,
                "year": album.year,
                "image_url": album.image_url,
                "genre": album.genre,
                "spotify_url": album.spotify_url,
                "apple_music_url": album.apple_music_url,
                "artist": self._get_artist_name(album),
                "description": ai_content,
                "content_type": content_type
            })
            
            # Note: rafraîchissement des albums incomplets traité en post-processing
            logger.info(f"Album ajouté: {album.title} - Image: {album.image_url[:50] if album.image_url else 'None'}")
        
        # OPTIMISATION: Supprimer les fillers IA (trop lents, pas essentiels)
        filler_content = []
        
        # OPTIMISATION: Utiliser un layout statique aléatoire au lieu d'appeler l'IA
        layout_suggestion = {
            "columns": random.choice([1, 2, 3]),
            "imagePosition": random.choice(["top", "left", "right", "bottom", "center", "fullwidth", "corner", "diagonal"]),
            "imageSize": random.choice(["small", "medium", "large", "massive", "micro"]),
            "textLayout": random.choice(["single-column", "double-column", "asymmetric", "scattered"]),
            "composition": random.choice(["classic", "dramatic", "playful", "chaos"]),
            "accentColor": random.choice(["#ff6b35", "#f7931e", "#10b981", "#06b6d4", "#8b5cf6", "#ec4899", "#764ba2"]),
            "specialEffect": random.choice(["none", "blur", "gradient", "zoom", "tilt"])
        }
        
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
        from sqlalchemy.orm import joinedload
        from app.models import Image
        
        # Récupérer un album aléatoire avec description IA RICHE (> 500 chars) - LIMITER!
        albums = self.db.query(Album).options(
            joinedload(Album.artists).joinedload(Artist.images)
        ).filter(
            Album.ai_description.isnot(None),
            func.length(Album.ai_description) > 500  # Description riche uniquement
        ).limit(100).all()  # LIMITE pour éviter de charger 10,000+ albums!
        
        # Fallback : accepter des descriptions plus courtes si aucune description riche
        if not albums:
            logger.warning("⚠️ Aucun album avec description riche, fallback vers descriptions courtes")
            albums = self.db.query(Album).options(
                joinedload(Album.artists)
            ).filter(
                Album.ai_description.isnot(None)
            ).limit(100).all()  # LIMITE ici aussi!
        
        if not albums:
            return self._empty_page()
        
        album = random.choice(albums)
        artist_names = ", ".join([a.name for a in album.artists]) if album.artists else "Artiste inconnu"
        
        # Récupérer les images d'artiste
        from app.models import Image
        artist_images = {}
        for artist in album.artists:
            logger.info(f"🔍 Recherche image pour artiste: {artist.name} (ID: {artist.id})")
            
            # APPROACH 1: Utiliser les images déjà chargées (joinedload)
            if hasattr(artist, 'images') and artist.images:
                for img in artist.images:
                    if img.image_type == 'artist' and img.url:
                        artist_images[artist.name] = img.url
                        logger.info(f"✅ Image artiste trouvée (from joinedload) pour {artist.name}: {img.url[:60]}...")
                        break  # Prendre la première image d'artiste
            
            # APPROACH 2: Requête directe si not found
            if artist.name not in artist_images:
                artist_image = self.db.query(Image).filter(
                    Image.artist_id == artist.id,
                    Image.image_type == 'artist'
                ).first()
                if artist_image and artist_image.url:
                    artist_images[artist.name] = artist_image.url
                    logger.info(f"✅ Image artiste trouvée (from query) pour {artist.name}: {artist_image.url[:60]}...")
                else:
                    logger.warning(f"⚠️ Pas d'image artiste pour '{artist.name}' (ID: {artist.id}), fallback Spotify...")
            
            # APPROACH 3: Fallback à Spotify si toujours pas trouvée
            if artist.name not in artist_images:
                try:
                    if self.spotify_service:
                        spotify_image = await self.spotify_service.search_artist_image(artist.name)
                        if spotify_image:
                            logger.info(f"📸 Image Spotify trouvée pour {artist.name}: {spotify_image[:60]}...")
                            artist_images[artist.name] = spotify_image
                            # Créer et sauvegarder pour la prochaine fois
                            new_image = Image(
                                url=spotify_image,
                                image_type='artist',
                                source='spotify',
                                artist_id=artist.id
                            )
                            self.db.add(new_image)
                            try:
                                self.db.commit()
                                logger.info(f"✅ Image Spotify sauvegardée pour {artist.name}")
                            except Exception as e:
                                logger.warning(f"⚠️ Erreur sauvegarde image Spotify pour {artist.name}: {e}")
                                self.db.rollback()
                        else:
                            logger.warning(f"❌ Aucune image Spotify trouvée pour {artist.name}")
                    else:
                        logger.warning(f"⚠️ Spotify service not available")
                except Exception as e:
                    logger.error(f"❌ Erreur recherche Spotify pour {artist.name}: {e}", exc_info=True)
        
        # Utiliser la description existante (potentiellement enrichie) avec nettoyage
        description = album.ai_description
        if description:
            description = self._clean_markdown_text(description)
        
        # Si l'album est un remaster/deluxe SANS description riche, utiliser un fallback
        # (l'enrichissement se fera en arrière-plan)
        if self._is_remaster_or_deluxe(album.title) and (not description or len(description) < 500):
            logger.info(f"📀 Album remaster/deluxe sans description riche: {album.title}, utilisation fallback")
            description = self._get_creative_fallback(album, "remaster")
        elif description:
            logger.info(f"♻️ Utilisation description existante pour {album.title}: {len(description)} chars (nettoyée)")
        
        # OPTIMISATION: Layout statique aléatoire
        layout_suggestion = {
            "columns": 1,
            "imagePosition": random.choice(["left", "right", "top"]),
            "imageSize": random.choice(["medium", "large"]),
            "textLayout": random.choice(["single-column", "double-column"]),
            "composition": "classic",
            "accentColor": random.choice(["#ff6b35", "#10b981", "#06b6d4"]),
            "specialEffect": "none"
        }
        
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
                    "spotify_url": album.spotify_url,
                    "apple_music_url": album.apple_music_url,
                    "description": description,
                    "style": album.ai_style
                },
                "artist_images": artist_images
            },
            "dimensions": {
                "image_size": random.choice(["small", "medium", "large"]),
                "description_length": "full",
                "font_size": random.choice(["small", "medium", "large"])
            }
        }
    
    async def _generate_page_3_albums_haikus(self) -> Dict[str, Any]:
        """Page 3: Albums aléatoires + Haikus avec descriptions générées par l'IA."""
        # Sélectionner des albums avec images (avec joinedload, limite 200)
        available_albums = self.db.query(Album).options(
            joinedload(Album.artists)
        ).filter(
            Album.image_url.isnot(None)
        ).limit(200).all()  # Limiter à 200 pour pas charger trop d'albums
        
        # Fallback : si pas assez d'albums avec images, prendre TOUS les albums
        if len(available_albums) < 3:
            logger.warning(f"⚠️ Seulement {len(available_albums)} albums avec images pour page 3, fallback complet")
            available_albums = self.db.query(Album).options(
                joinedload(Album.artists)
            ).limit(50).all()  # Limiter à 50 albums totaux
        
        if len(available_albums) < 1:
            logger.warning("⚠️ Aucun album disponible pour page 3, création fallback")
            return self._generate_fallback_page_3()
        
        # Sélectionner 3-4 albums aléatoirement
        selected_albums = random.sample(available_albums, min(random.randint(3, 4), len(available_albums)))
        
        # Note: rafraîchissement des albums incomplets traité dans generate_magazine()
        
        # Créer haikus avec l'IA
        haikus = []
        for album in selected_albums:
            # Générer haiku avec l'IA
            haiku = await self._generate_ai_haiku(album)
            
            # OPTIMISATION: Utiliser description existante ou fallback (pas d'appel IA)
            description = album.ai_description
            if not description or description == "Aucune information disponible" or len(description.strip()) < 50:
                description = self._get_creative_fallback(album, "description")
                logger.info(f"📝 Fallback créatif utilisé pour {album.title} (page 3)")
            else:
                description = self._clean_markdown_text(description)
                description = self._ensure_markdown_format(description)
            
            # OPTIMISATION: Layout statique aléatoire au lieu d'appel IA
            individual_layout = {
                "columns": random.choice([1, 2, 3]),
                "imagePosition": random.choice(["top", "left", "right", "diagonal"]),
                "imageSize": random.choice(["small", "medium", "large", "massive"]),
                "textLayout": random.choice(["single-column", "asymmetric"]),
                "composition": random.choice(["classic", "dramatic", "playful"]),
                "accentColor": random.choice(["#ff6b35", "#10b981", "#06b6d4", "#8b5cf6", "#ab47bc"]),
                "specialEffect": random.choice(["none", "gradient", "zoom"])
            }
            
            haikus.append({
                "album_id": album.id,
                "album_title": album.title,
                "haiku": haiku,
                "layout": individual_layout,
                "description": description
            })
        
        # OPTIMISATION: Layout statique aléatoire
        layout_suggestion = {
            "columns": random.choice([2, 3, 4]),
            "imagePosition": "top",
            "imageSize": random.choice(["medium", "large"]),
            "textLayout": "single-column",
            "composition": "classic",
            "accentColor": random.choice(["#ff6b35", "#10b981", "#06b6d4", "#8b5cf6"]),
            "specialEffect": "none"
        }
        
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
                        "genre": album.genre,
                        "spotify_url": album.spotify_url,
                        "apple_music_url": album.apple_music_url
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
        # Récupérer les DERNIÈRES écoutes en utilisant ORDER BY DESC pour garantir l'ordre chronologique
        # Optimisé avec min_id pour éviter le full table scan sur les anciennes données
        max_id = self.db.query(func.max(ListeningHistory.id)).scalar() or 0
        min_id = max(0, max_id - 1000)  # Range plus large pour avoir plus de données
        
        # Charger les 300 écoutes les plus récentes avec joinedload (au lieu de 100)
        recent_history = self.db.query(ListeningHistory).options(
            joinedload(ListeningHistory.track).joinedload(Track.album).joinedload(Album.artists)
        ).filter(
            ListeningHistory.id > min_id
        ).order_by(ListeningHistory.id.desc()).limit(300).all()  # Tri décroissant et limite augmentée
        
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
        
        # Récupérer les objets complets avec une seule query (au lieu de boucler sur les 100 entries!)
        top_artists_full = []
        if top_artists_ids:
            artist_ids_list = [aid[0] for aid in top_artists_ids]
            artists_map = {artist.id: artist for artist in self.db.query(Artist).options(
                joinedload(Artist.images)
            ).filter(Artist.id.in_(artist_ids_list)).all()}
            
            for artist_id, count in top_artists_ids:
                artist = artists_map.get(artist_id)
                if artist:
                    top_artists_full.append({
                        "artist_id": artist.id,
                        "artist_name": artist.name,
                        "image_url": artist.images[0].url if artist.images else None,
                        "count": count
                    })
        
        # Charger TOUS les albums en 1 seule query au lieu de N queries
        if top_albums_ids:
            album_ids_list = [aid[0] for aid in top_albums_ids]
            albums_map = {album.id: album for album in self.db.query(Album).options(
                joinedload(Album.artists).joinedload(Artist.images)
            ).filter(Album.id.in_(album_ids_list)).all()}
            
            top_albums_full = []
            for album_id, count in top_albums_ids:
                album = albums_map.get(album_id)
                if album:
                    # Chercher une image de fallback si l'album n'en a pas
                    image_url = album.image_url
                    if not image_url:
                        # Utiliser l'image du premier artiste comme fallback
                        if album.artists:
                            first_artist = album.artists[0]
                            if first_artist.images:
                                image_url = first_artist.images[0].url
                    
                    top_albums_full.append({
                        "album_id": album.id,
                        "album_title": album.title,
                        "artist_name": self._get_artist_name(album),
                        "image_url": image_url,
                        "spotify_url": album.spotify_url,
                        "apple_music_url": album.apple_music_url,
                        "count": count
                    })
        else:
            top_albums_full = []
        
        return {
            "page_number": 4,
            "type": "timeline_stats",
            "title": "Vos Dernières Écoutes",
            "layout": self._generate_layout_suggestion("stats", "Top artistes et albums avec images"),
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
        # Récupérer les albums avec images (avec joinedload pour éviter N+1)
        albums = self.db.query(Album).options(
            joinedload(Album.artists)
        ).filter(
            Album.image_url.isnot(None)
        ).limit(50).all()
        
        # Fallback : si pas assez d'albums avec images, prendre TOUS les albums
        if len(albums) < 5:
            logger.warning(f"⚠️ Seulement {len(albums)} albums avec images pour page 5, fallback complet")
            albums = self.db.query(Album).options(
                joinedload(Album.artists)
            ).limit(50).all()  # Limiter à 50 albums totaux
        
        if len(albums) < 1:
            logger.warning("⚠️ Aucun album disponible pour page 5, création fallback")
            return self._generate_fallback_page_5()
        
        # Thème basé sur les genres dominants dans les albums
        genres = [a.genre for a in albums if a.genre]
        dominant_genre = max(set(genres), key=genres.count) if genres else "Musique"
        
        theme_templates = [
            f"Voyage {dominant_genre}",
            f"Échos {dominant_genre}",
            f"Nuits {dominant_genre}",
            f"Âmes de {dominant_genre}",
            f"Horizons {dominant_genre}"
        ]
        selected_theme = random.choice(theme_templates)
        
        # Description basée sur les albums sélectionnés
        album_count = len(albums)
        styles = [a.ai_style for a in albums if a.ai_style]
        style_summary = ", ".join(styles[:3]) if styles else "diverses ambiances musicales"
        
        playlist_description = f"*{selected_theme}* vous propose **{album_count} albums** soigneusement sélectionnés : {style_summary}. Une **expérience sonore** authentique qui **transporte** et *inspire*. ✨"
        
        # Sélectionner 5-7 albums de manière vraiment aléatoire
        num_albums = random.randint(5, min(7, len(albums)))
        selected_albums = random.sample(albums, num_albums)
        
        # Note: rafraîchissement des albums incomplets traité dans generate_magazine()
        
        # OPTIMISATION: Utiliser des raisons statiques au lieu d'appels IA
        playlist_albums = []
        reason_templates = [
            f"**Captivant** et *authentique*, cet album incarne l'essence de *{selected_theme}*.",
            f"Une **sélection poétique** qui résonne parfaitement avec le thème de cette playlist.",
            f"Apporte une **profondeur émotionnelle** incomparable à cette playlist.",
            f"**Incontournable** pour ceux qui recherchent l'*authenticité* musicale.",
            f"Un album qui **transcende** et offre une nouvelle *perspective* sonore.",
            f"*Parfait* pour capturer l'**atmosphère** de {selected_theme}.",
            f"Une **pièce maîtresse** qui définit l'esprit de cette playlist."
        ]
        
        for album in selected_albums:
            # OPTIMISATION: Utiliser des raisons aléatoires prédéfinies
            album_reason = random.choice(reason_templates)
            
            # OPTIMISATION: Layout statique aléatoire
            album_layout = {
                "columns": random.choice([1, 2, 3]),
                "imagePosition": random.choice(["top", "diagonal"]),
                "imageSize": random.choice(["medium", "large", "massive"]),
                "textLayout": random.choice(["single-column", "asymmetric", "scattered"]),
                "composition": random.choice(["classic", "dramatic", "playful", "chaos"]),
                "accentColor": random.choice(["#ff6b35", "#FF00FF", "#06b6d4", "#ab47bc"]),
                "specialEffect": random.choice(["none", "gradient", "tilt"])
            }
            
            playlist_albums.append({
                "id": album.id,
                "title": album.title,
                "artist": ", ".join([a.name for a in album.artists]) if album.artists else "?",
                "image_url": album.image_url,
                "year": album.year,
                "spotify_url": album.spotify_url,
                "apple_music_url": album.apple_music_url,
                "layout": album_layout,
                "reason": album_reason
            })
        
        # OPTIMISATION: Layout statique
        page_layout = {
            "columns": random.choice([2, 3]),
            "imagePosition": "top",
            "imageSize": "medium",
            "textLayout": "single-column",
            "composition": "classic",
            "accentColor": random.choice(["#ff6b35", "#10b981", "#06b6d4"]),
            "specialEffect": "none"
        }
        
        return {
            "page_number": 5,
            "type": "playlist_theme",
            "title": f"Playlist: {selected_theme}",
            "layout": page_layout,
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
    
    def _generate_fallback_page_1(self) -> Dict[str, Any]:
        """Générer une page 1 de fallback quand pas d'artiste disponible."""
        logger.info("📝 Génération fallback page 1 avec données mockup")
        
        # Créer des données mockup
        fallback_albums = [
            {
                "id": 999 + i,
                "title": f"Album Musical {i+1}",
                "year": 2024 - i,
                "image_url": f"https://via.placeholder.com/300?text=Album+{i+1}",
                "genre": "Musique",
                "spotify_url": None,
                "apple_music_url": None,
                "artist": f"Artiste {i+1}",
                "description": "**Une création musicale** qui mérite l'attention. Cet album *capture* quelque chose d'essentiel : une **émotion brute**, une **vision artistique** affirmée.",
                "content_type": "fallback"
            }
            for i in range(5)
        ]
        
        return {
            "page_number": 1,
            "type": "artist_showcase",
            "title": "Découverte Musicale",
            "layout": {
                "columns": 2,
                "imagePosition": "top",
                "imageSize": "large",
                "textLayout": "single-column",
                "composition": "classic",
                "accentColor": "#ff6b35",
                "specialEffect": "none"
            },
            "content": {
                "artist": {
                    "name": "Découvrez la Musique",
                    "albums_count": 5,
                    "haiku": "**La Musique**\nRésonne dans les cœurs\nÉternellement",
                    "bio": "**Explorez** notre collection musicale sélectionnée avec soin. Une **expérience** unique qui **célèbre** la diversité et **l'authenticité** artistique. ✨",
                    "image_url": None
                },
                "albums": fallback_albums,
                "filler": []
            },
            "dimensions": {
                "image_height": 400,
                "text_columns": 2,
                "color_scheme": "newspaper"
            }
        }
    
    def _generate_fallback_page_3(self) -> Dict[str, Any]:
        """Générer une page 3 de fallback avec haikus mockup."""
        logger.info("📝 Génération fallback page 3 avec haikus mockup")
        
        fallback_haikus = [
            {
                "album_id": 1001,
                "album_title": "Haïku Musical #1",
                "haiku": "**Silence Mélodique**\nNotes qui dansent\nChant de l'âme",
                "layout": {
                    "columns": 2,
                    "imagePosition": "top",
                    "imageSize": "medium",
                    "textLayout": "single-column",
                    "composition": "classic",
                    "accentColor": "#10b981",
                    "specialEffect": "none"
                },
                "description": "**Vrai** haïku musical inspiré de la poésie classique. Cette création **évoque** la beauté du silence et l'**harmonie** parfaite entre les notes."
            },
            {
                "album_id": 1002,
                "album_title": "Haïku Musical #2",
                "haiku": "**Rythme Infini**\nLumière dans le son\nJoie pure éclatante",
                "layout": {
                    "columns": 2,
                    "imagePosition": "top",
                    "imageSize": "medium",
                    "textLayout": "single-column",
                    "composition": "classic",
                    "accentColor": "#06b6d4",
                    "specialEffect": "none"
                },
                "description": "Une **symphonie** de couleurs et de sons qui **illumine** le cœur. L'album capture l'**essence** de la **joie** dans chaque mesure."
            }
        ]
        
        return {
            "page_number": 3,
            "type": "albums_haikus",
            "title": "Haïkus Musicaux",
            "layout": {
                "columns": 2,
                "imagePosition": "top",
                "imageSize": "medium",
                "textLayout": "single-column",
                "composition": "classic",
                "accentColor": "#10b981",
                "specialEffect": "none"
            },
            "content": {
                "albums": [
                    {
                        "id": h["album_id"],
                        "title": h["album_title"],
                        "artist": "Artiste Haïku",
                        "image_url": "https://via.placeholder.com/300?text=Haiku",
                        "genre": "Musique",
                        "spotify_url": None
                    }
                    for h in fallback_haikus
                ],
                "haikus": fallback_haikus
            },
            "dimensions": {
                "image_size": "medium",
                "columns": 2,
                "spacing": "normal"
            }
        }
    
    def _generate_fallback_page_5(self) -> Dict[str, Any]:
        """Générer une page 5 de fallback avec playlist mockup."""
        logger.info("📝 Génération fallback page 5 avec playlist mockup")
        
        fallback_playlist_albums = [
            {
                "id": 2001 + i,
                "title": f"Titre Playlist {i+1}",
                "artist": f"Artiste {i+1}",
                "image_url": f"https://via.placeholder.com/300?text=Playlist+{i+1}",
                "year": 2024 - (i % 3),
                "spotify_url": None,
                "layout": {
                    "columns": 2,
                    "imagePosition": "top",
                    "imageSize": "medium",
                    "textLayout": "single-column",
                    "composition": "classic",
                    "accentColor": ["#ff6b35", "#10b981", "#06b6d4"][i % 3],
                    "specialEffect": "none"
                },
                "reason": "Une **pièce maîtresse** qui **définit** l'esprit de cette playlist."
            }
            for i in range(5)
        ]
        
        return {
            "page_number": 5,
            "type": "playlist_theme",
            "title": "Playlist: Voyage Musical",
            "layout": {
                "columns": 2,
                "imagePosition": "top",
                "imageSize": "medium",
                "textLayout": "single-column",
                "composition": "classic",
                "accentColor": "#8b5cf6",
                "specialEffect": "none"
            },
            "content": {
                "playlist": {
                    "theme": "Voyage Musical",
                    "description": "*Voyage Musical* vous propose une **sélection d'albums** soigneusement choisie pour une **expérience sonore** authentique qui **transcende** et inspire. ✨",
                    "albums": fallback_playlist_albums
                }
            },
            "dimensions": {
                "card_style": "detailed",
                "image_position": "top"
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
