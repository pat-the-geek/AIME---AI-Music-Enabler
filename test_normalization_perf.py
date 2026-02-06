#!/usr/bin/env python3
"""Test normalization performance."""
import time
import sys
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.services.roon_normalization_service import RoonNormalizationService

def main():
    # Create DB session
    db = SessionLocal()
    
    try:
        service = RoonNormalizationService()
        
        # Test 1: Quick test with limit=10
        print("=" * 60)
        print("🚀 Test 1: Quick normalization with limit=10")
        print("=" * 60)
        
        start = time.time()
        results = service.simulate_normalization(db, limit=10)
        elapsed = time.time() - start
        
        print(f"✅ Quick test completed in {elapsed:.2f} seconds")
        print(f"   - Artists total: {results['stats']['artists_total']}")
        print(f"   - Would update: {results['stats']['artists_would_update']}")
        print(f"   - Albums total: {results['stats']['albums_total']}")
        print(f"   - Would update: {results['stats']['albums_would_update']}")
        
        # Test 2: Full test
        print("\n" + "=" * 60)
        print("⚡ Test 2: Full normalization (all artists/albums)")
        print("=" * 60)
        print("(This may take a moment...)")
        
        start = time.time()
        results_full = service.simulate_normalization(db, limit=None)
        elapsed_full = time.time() - start
        
        print(f"✅ Full test completed in {elapsed_full:.2f} seconds")
        print(f"   - Artists total: {results_full['stats']['artists_total']}")
        print(f"   - Would update: {results_full['stats']['artists_would_update']}")
        print(f"   - Albums total: {results_full['stats']['albums_total']}")
        print(f"   - Would update: {results_full['stats']['albums_would_update']}")
        
        # Performance summary
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Quick mode (limit=10):  {elapsed:.3f}s")
        print(f"Full mode (all data):   {elapsed_full:.3f}s")
        print(f"Target:                 <1s for full mode")
        print(f"Status:                 {'✅ PASS' if elapsed_full < 1.0 else '⚠️  SLOW'}")
        
        # Write results to file
        with open('normalization_test_results.txt', 'w') as f:
            f.write(f"Quick mode (limit=10): {elapsed:.3f}s\n")
            f.write(f"Full mode (all data): {elapsed_full:.3f}s\n")
            f.write(f"Target: <1s for full mode\n")
            f.write(f"Status: {'PASS' if elapsed_full < 1.0 else 'SLOW'}\n")
            f.write(f"\nFull results:\n{results_full}\n")
        
        print("\nResults saved to normalization_test_results.txt")
        
    finally:
        db.close()

if __name__ == '__main__':
    main()
