"""Modèle Metadata (métadonnées supplémentaires)."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Metadata(Base):
    """Modèle pour les métadonnées supplémentaires."""
    
    __tablename__ = "metadata"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    album_id = Column(Integer, ForeignKey('albums.id', ondelete='CASCADE'), nullable=False, unique=True)
    ai_info = Column(Text, nullable=True)  # Description générée par IA (500 chars max)
    resume = Column(Text, nullable=True)  # Résumé long (Discogs/IA)
    labels = Column(Text, nullable=True)  # JSON array: ["Label1", "Label2"]
    film_title = Column(String(500), nullable=True)  # Si BOF: titre du film
    film_year = Column(Integer, nullable=True)  # Si BOF: année du film
    film_director = Column(String(255), nullable=True)  # Si BOF: réalisateur
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    album = relationship("Album", back_populates="album_metadata")
    
    __table_args__ = (
        Index('idx_metadata_album', 'album_id'),
        Index('idx_metadata_film', 'film_title'),
        Index('idx_metadata_film_year', 'film_year'),
    )
    
    def __repr__(self):
        return f"<Metadata(id={self.id}, album_id={self.album_id})>"
