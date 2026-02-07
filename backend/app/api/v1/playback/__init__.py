"""Playback domain routes."""
from app.api.v1.playback.playlists import router as playlists_router
from app.api.v1.playback.roon import router as roon_router

__all__ = ["playlists_router", "roon_router"]
