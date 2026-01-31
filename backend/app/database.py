"""Configuration de la base de données SQLAlchemy."""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configuration du pool de connexions
if settings.database_url.startswith("sqlite"):
    # SQLite: utiliser StaticPool pour éviter les problèmes de concurrence
    pool_config = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False, "timeout": 30},
    }
else:
    # Autres bases: utiliser QueuePool pour gérer les connexions
    pool_config = {
        "poolclass": QueuePool,
        "pool_size": 20,
        "max_overflow": 30,
        "pool_pre_ping": True,  # Vérifier les connexions avant usage
        "pool_recycle": 3600,  # Recycler les connexions toutes les heures
    }

# Créer le moteur SQLAlchemy
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    **pool_config
)

# Event listeners pour la gestion des erreurs
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Configuration des connexions."""
    if settings.database_url.startswith("sqlite"):
        dbapi_conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging pour SQLite
        dbapi_conn.execute("PRAGMA synchronous = NORMAL")
        dbapi_conn.execute("PRAGMA cache_size = 10000")

@event.listens_for(engine, "engine_disposed")
def receive_engine_disposed(engine):
    """Log quand le moteur est fermé."""
    logger.info("Moteur de base de données fermé")

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
