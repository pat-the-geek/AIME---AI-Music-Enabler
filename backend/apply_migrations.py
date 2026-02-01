#!/usr/bin/env python3
"""Script pour appliquer les migrations de base de données."""

import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migrations():
    """Appliquer toutes les migrations pending."""
    db = SessionLocal()
    try:
        # Créer la table alembic_version si elle n'existe pas
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """))
        db.commit()
        
        # Vérifier la version actuelle
        result = db.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1")).fetchone()
        current_version = result[0] if result else None
        logger.info(f"📊 Version actuelle: {current_version or 'None'}")
        
        # Appliquer manuellement les migrations
        migrations = [
            ('001_add_source_column', '001'),
            ('002_fix_invalid_supports', '002'),
            ('003_add_service_states', '003')
        ]
        
        for migration_name, revision_id in migrations:
            # Vérifier si la migration a déjà été appliquée
            result = db.execute(text(f"SELECT version_num FROM alembic_version WHERE version_num = '{revision_id}'")).fetchone()
            if result:
                logger.info(f"✓ Migration {migration_name} déjà appliquée")
                continue
            
            # Charger et exécuter la migration
            try:
                module_path = f"alembic.versions.{revision_id}_{migration_name.replace(revision_id + '_', '')}"
                migration_module = __import__(module_path, fromlist=['upgrade'])
                
                logger.info(f"🔄 Application de la migration: {migration_name}")
                migration_module.upgrade()
                
                # Marquer comme appliquée
                db.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{revision_id}')"))
                db.commit()
                logger.info(f"✅ Migration {migration_name} appliquée avec succès")
            except ImportError as e:
                logger.warning(f"⚠️ Impossible de charger la migration {migration_name}: {e}")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'application de {migration_name}: {e}")
                db.rollback()
                raise
        
        logger.info("✅ Toutes les migrations ont été appliquées!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des migrations: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    apply_migrations()
