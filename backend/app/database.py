"""Configuration de la base de données SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

# Créer le moteur SQLAlchemy
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Nécessaire pour SQLite
    echo=settings.database_echo,
)

# Session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def get_db():
    """Dépendance pour obtenir une session DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialiser la base de données (créer les tables)."""
    # Créer le répertoire de données si nécessaire
    import os
    from pathlib import Path
    
    # Extraire le chemin du fichier depuis l'URL SQLite
    db_url = str(settings.database_url)
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
