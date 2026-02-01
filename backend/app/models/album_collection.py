"""Modèle AlbumCollection (collections d'albums)."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AlbumCollection(Base):
    """Modèle pour les collections d'albums."""
    
    __tablename__ = "album_collections"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    search_type = Column(String(50), nullable=False)  # 'genre', 'artist', 'period', 'ai_query', 'custom'
    search_criteria = Column(Text, nullable=True)  # JSON avec les critères de recherche
    ai_query = Column(Text, nullable=True)  # Requête en langage naturel pour recherche AI
    album_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    albums = relationship("CollectionAlbum", back_populates="collection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AlbumCollection(id={self.id}, name='{self.name}', type='{self.search_type}')>"


class CollectionAlbum(Base):
    """Modèle pour les albums dans les collections."""
    
    __tablename__ = "collection_albums"
    
    collection_id = Column(Integer, ForeignKey('album_collections.id', ondelete='CASCADE'), primary_key=True)
    album_id = Column(Integer, ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True)
    position = Column(Integer, nullable=False)
    
    # Relations
    collection = relationship("AlbumCollection", back_populates="albums")
    album = relationship("Album")
    
    def __repr__(self):
        return f"<CollectionAlbum(collection_id={self.collection_id}, album_id={self.album_id}, pos={self.position})>"
