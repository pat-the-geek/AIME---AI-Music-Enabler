"""Schémas de l'application."""
from app.schemas.artist import (
    ArtistBase,
    ArtistCreate,
    ArtistUpdate,
    ArtistResponse,
    ArtistWithImage,
)
from app.schemas.album import (
    AlbumBase,
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    AlbumDetail,
    AlbumListResponse,
)
from app.schemas.track import (
    TrackBase,
    TrackCreate,
    TrackUpdate,
    TrackResponse,
)
from app.schemas.history import (
    ListeningHistoryBase,
    ListeningHistoryCreate,
    ListeningHistoryUpdate,
    ListeningHistoryResponse,
    ListeningHistoryListResponse,
    TimelineResponse,
    StatsResponse,
)
from app.schemas.playlist import (
    PlaylistAlgorithm,
    PlaylistCreate,
    PlaylistGenerate,
    PlaylistTrackResponse,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistExportFormat,
)

__all__ = [
    "ArtistBase",
    "ArtistCreate",
    "ArtistUpdate",
    "ArtistResponse",
    "ArtistWithImage",
    "AlbumBase",
    "AlbumCreate",
    "AlbumUpdate",
    "AlbumResponse",
    "AlbumDetail",
    "AlbumListResponse",
    "TrackBase",
    "TrackCreate",
    "TrackUpdate",
    "TrackResponse",
    "ListeningHistoryBase",
    "ListeningHistoryCreate",
    "ListeningHistoryUpdate",
    "ListeningHistoryResponse",
    "ListeningHistoryListResponse",
    "TimelineResponse",
    "StatsResponse",
    "PlaylistAlgorithm",
    "PlaylistCreate",
    "PlaylistGenerate",
    "PlaylistTrackResponse",
    "PlaylistResponse",
    "PlaylistDetailResponse",
    "PlaylistExportFormat",
]
