"""Modèle Image (URLs d'images)."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Image(Base):
    """Modèle pour les URLs d'images."""
    
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String(1000), nullable=False)
    image_type = Column(String(50), nullable=False)  # 'artist', 'album'
    source = Column(String(50), nullable=False)  # 'spotify', 'lastfm', 'discogs'
    artist_id = Column(Integer, ForeignKey('artists.id', ondelete='CASCADE'), nullable=True)
    album_id = Column(Integer, ForeignKey('albums.id', ondelete='CASCADE'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    artist = relationship("Artist", back_populates="images")
    album = relationship("Album", back_populates="images")
    
    __table_args__ = (
        CheckConstraint(
            '(artist_id IS NOT NULL AND album_id IS NULL) OR (artist_id IS NULL AND album_id IS NOT NULL)',
            name='check_single_entity'
        ),
        Index('idx_image_artist', 'artist_id'),
        Index('idx_image_album', 'album_id'),
    )
    
    def __repr__(self):
        entity_type = "artist" if self.artist_id else "album"
        entity_id = self.artist_id if self.artist_id else self.album_id
        return f"<Image(id={self.id}, type='{self.image_type}', {entity_type}_id={entity_id})>"
