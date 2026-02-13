"""API v1 routes - organized by domain."""
# Collection domain
from app.api.v1.collection import albums_router, album_collections_router, artists_router

# Content domain
from app.api.v1.content import history_router

# Playback domain
from app.api.v1.playback import playlists_router

# Tracking domain
from app.api.v1.tracking import services_router

# Analytics domain
from app.api.v1.analytics import analytics_router

# Magazines domain
from app.api.v1.magazines import magazines_router

# Search domain
from app.api.v1.search import search_router

# Create legacy module-like objects for backward compatibility
class _ModuleWrapper:
    """Wrapper to provide .router attribute."""
    def __init__(self, router):
        self.router = router

collection = _ModuleWrapper(albums_router)
artists = _ModuleWrapper(artists_router)
collections = _ModuleWrapper(album_collections_router)
history = _ModuleWrapper(history_router)
playlists = _ModuleWrapper(playlists_router)
services = _ModuleWrapper(services_router)
analytics = _ModuleWrapper(analytics_router)
magazines = _ModuleWrapper(magazines_router)
search = _ModuleWrapper(search_router)

__all__ = [
    "collection",
    "artists",
    "collections",
    "history",
    "playlists",
    "services",
    "analytics",
    "magazines",
    "search",
]
