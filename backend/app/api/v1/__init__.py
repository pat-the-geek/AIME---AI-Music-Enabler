"""Fichier __init__ pour les routes API v1."""
from app.api.v1 import collection, history, playlists, services, search

__all__ = ["collection", "history", "playlists", "services", "search"]
