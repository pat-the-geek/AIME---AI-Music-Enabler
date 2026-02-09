#!/usr/bin/env python3
"""Apply DESC indexes for listening_history performance optimization."""

import sys
import os
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_desc_indexes():
    """Apply descending indexes to listening_history table."""
    db = SessionLocal()
    try:
        logger.info("📊 Applying DESC indexes for Journal performance...")
        
        # Check if indexes already exist
        indexes_to_create = [
            ('idx_history_timestamp_desc', 'listening_history', 'timestamp DESC'),
            ('idx_history_timestamp_source_desc', 'listening_history (timestamp DESC, source)'),
            ('idx_history_timestamp_loved_desc', 'listening_history (timestamp DESC, loved)'),
        ]
        
        # Create indexes
        index_sql = [
            "CREATE INDEX IF NOT EXISTS idx_history_timestamp_desc ON listening_history(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_history_timestamp_source_desc ON listening_history(timestamp DESC, source)",
            "CREATE INDEX IF NOT EXISTS idx_history_timestamp_loved_desc ON listening_history(timestamp DESC, loved)",
        ]
        
        for sql in index_sql:
            try:
                db.execute(text(sql))
                index_name = sql.split("IF NOT EXISTS ")[-1].split(" ON")[0]
                logger.info(f"✓ Created index: {index_name}")
            except Exception as e:
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info(f"✓ Index already exists (skipping)")
                else:
                    logger.warning(f"⚠ Index creation warning: {e}")
        
        db.commit()
        
        # Verify indexes were created
        logger.info("\n📋 Verification - Checking created indexes:")
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_history%'
            ORDER BY name
        """)).fetchall()
        
        for row in result:
            logger.info(f"  ✓ {row[0]}")
        
        logger.info(f"\n✅ DESC indexes applied successfully! {len(result)} indexes found.")
        
    except Exception as e:
        logger.error(f"❌ Error applying indexes: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    apply_desc_indexes()
