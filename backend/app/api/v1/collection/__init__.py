"""Collection domain routes."""
from app.api.v1.collection.albums import router as albums_router
from app.api.v1.collection.album_collections import router as album_collections_router
from app.api.v1.collection.artists import router as artists_router

__all__ = ["albums_router", "album_collections_router", "artists_router"]
