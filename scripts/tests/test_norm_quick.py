#!/usr/bin/env python3
import time
import sys
import logging
sys.path.insert(0, 'backend')

# Suppress logs
logging.getLogger().setLevel(logging.CRITICAL)

from app.database import SessionLocal
from app.services.roon_normalization_service import RoonNormalizationService

db = SessionLocal()
service = RoonNormalizationService()

try:
    # Quick test
    print("Testing limit=10...")
    start = time.time()
    r1 = service.simulate_normalization(db, limit=10)
    t1 = time.time() - start
    print(f"Quick: {t1:.3f}s")
    
   # Full test
    print("Testing full... (this takes a while)")
    start = time.time()
    r2 = service.simulate_normalization(db, limit=None)
    t2 = time.time() - start
    print(f"Full: {t2:.3f}s")
    print(f"\nStatus: {'PASS ✅' if t2 < 1.0 else 'SLOW ⚠️'}")
    print(f"Target: <1s (got {t2:.3f}s)")
finally:
    db.close()
