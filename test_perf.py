import time, sys
sys.path.insert(0, 'backend')
import logging
logging.getLogger().setLevel(logging.CRITICAL)

from app.database import SessionLocal
from app.services.roon_normalization_service import RoonNormalizationService

try:
    db = SessionLocal()
    svc = RoonNormalizationService()
    
    print("Quick test...", end='', flush=True)
    s = time.time()
    r1 = svc.simulate_normalization(db, limit=10)
    t1 = time.time() - s
    print(f" {t1:.3f}s")
    
    print("Full test...", end='', flush=True)
    s = time.time()
    r2 = svc.simulate_normalization(db)
    t2 = time.time() - s
    print(f" {t2:.3f}s")
    
    status = '✅ PASS' if t2 < 1.0 else '⚠️  SLOW'
    print(f"\nResult: {status} ({t2:.3f}s, target <1s)")
    
    with open('perf_result.txt', 'w') as f:
        f.write(f"Quick: {t1:.3f}s\nFull: {t2:.3f}s\nStatus: {'PASS' if t2 < 1.0 else 'SLOW'}\n")
    
finally:
    db.close()
