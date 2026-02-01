"""Fichier __init__ pour les routes API v1."""
from app.api.v1 import collection, history, services, search, collections
# from app.api.v1 import playlists  # Temporairement désactivé pendant la migration

__all__ = ["collection", "history", "services", "search", "collections"]
