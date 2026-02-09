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
    """Configuration des connexions SQLite pour post-wake recovery.
    
    Appelé à chaque nouvelle connexion (y compris après reconnexion suite à wake-up).
    Configure WAL mode (meilleure concurrence post-wake) et les pragmas de performance.
    """
    if settings.database_url.startswith("sqlite"):
        # WAL mode: permet lecture/écriture simultanées
        dbapi_conn.execute("PRAGMA journal_mode = WAL")
        # Timeout: augmentée pour post-wake-up (connexion peut être lente)
        dbapi_conn.execute("PRAGMA busy_timeout = 30000")  # 30 secondes en millisecondes
        # Performance
        dbapi_conn.execute("PRAGMA synchronous = NORMAL")
        dbapi_conn.execute("PRAGMA cache_size = 10000")
        logger.debug("🔌 SQLite connection configured: WAL mode, 30s timeout, cache 10MB")

@event.listens_for(engine, "engine_disposed")
def receive_engine_disposed(engine):
    """Log quand le moteur est fermé (ex: après wake-up)."""
    logger.info("🔌 Moteur de base de données fermé - nouvelle connexion au prochain accès")

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
