#!/usr/bin/env python3
"""Script pour créer la table service_states."""

import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_service_states_table():
    """Créer la table service_states si elle n'existe pas."""
    db = SessionLocal()
    try:
        # Vérifier si la table existe déjà
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='service_states'
        """)).fetchone()
        
        if result:
            logger.info("✓ Table service_states existe déjà")
            return
        
        # Créer la table
        logger.info("🔄 Création de la table service_states...")
        db.execute(text("""
            CREATE TABLE service_states (
                service_name VARCHAR NOT NULL PRIMARY KEY,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Créer l'index
        db.execute(text("""
            CREATE INDEX idx_service_states_last_updated 
            ON service_states (last_updated)
        """))
        
        db.commit()
        logger.info("✅ Table service_states créée avec succès!")
        
        # Vérifier la création
        result = db.execute(text("SELECT COUNT(*) FROM service_states")).fetchone()
        logger.info(f"✅ Table vérifiée: {result[0]} enregistrements")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de la table: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_service_states_table()
