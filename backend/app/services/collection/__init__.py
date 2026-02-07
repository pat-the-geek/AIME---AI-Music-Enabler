"""Collection & Library services (Albums, Artists, Exports, Stats)."""

from app.services.collection.album_service import AlbumService
from app.services.collection.artist_service import ArtistService
from app.services.collection.stats_service import CollectionStatsService
from app.services.collection.export_service import ExportService

# Services for managing the music collection
# - Album operations (CRUD, pagination, filtering)
# - Artist operations and metadata
# - Collection statistics and analytics
# - Exports (Markdown, JSON)

__all__ = [
    "AlbumService",
    "ArtistService",
    "CollectionStatsService",
    "ExportService",
]
