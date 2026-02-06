"""Modèles de l'application."""
from app.models.artist import Artist
from app.models.album import Album
from app.models.album_artist import album_artist
from app.models.track import Track
from app.models.listening_history import ListeningHistory
from app.models.image import Image
from app.models.metadata import Metadata
from app.models.album_collection import AlbumCollection, CollectionAlbum
from app.models.service_state import ServiceState
from app.models.scheduled_task_execution import ScheduledTaskExecution

__all__ = [
    "Artist",
    "Album",
    "album_artist",
    "Track",
    "ListeningHistory",
    "Image",
    "Metadata",
    "AlbumCollection",
    "CollectionAlbum",
    "ServiceState",
    "ScheduledTaskExecution",
]
