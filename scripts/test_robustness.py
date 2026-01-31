#!/usr/bin/env python3
"""
Script de test pour les améliorations de robustesse.
Teste les scénarios courants d'erreur.
"""

import asyncio
import sys
import os

# Ajouter backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import httpx
from app.core.retry import CircuitBreaker, RetryConfig
from app.core.exceptions import AIServiceException, DiscogsServiceException


def test_circuit_breaker():
    """Tester le circuit breaker."""
    print("\n🧪 Test 1: Circuit Breaker")
    print("=" * 60)
    
    cb = CircuitBreaker("TestService", failure_threshold=3, success_threshold=2, timeout=10)
    
    # Simuler des failures
    print("Recording 3 failures...")
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    
    assert cb.state == "OPEN", "Circuit breaker devrait être OUVERT"
    print(f"✅ Circuit breaker OUVERT après {cb.failure_threshold} failures")
    
    # Tester que les appels sont bloqués
    try:
        cb.call(lambda: 1/0)  # Appel est bloqué avant execution
        assert False, "Devrait lever CircuitBreakerOpen"
    except Exception as e:
        assert "Circuit breaker" in str(e)
        print(f"✅ Appels bloqués: {e}")
    
    # Simuler recovery
    cb._half_open()
    assert cb.state == "HALF_OPEN"
    print(f"✅ Circuit breaker passé en HALF_OPEN")
    
    # Succès → fermeture
    cb.record_success()
    cb.record_success()
    assert cb.state == "CLOSED"
    print(f"✅ Circuit breaker FERMÉ après {cb.success_threshold} succès")
    print()


def test_retry_config():
    """Tester la configuration du retry."""
    print("🧪 Test 2: Retry Config")
    print("=" * 60)
    
    config = RetryConfig(
        max_attempts=3,
        initial_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=False  # Sans jitter pour test
    )
    
    # Tester les délais
    delay_0 = config.get_delay(0)
    delay_1 = config.get_delay(1)
    delay_2 = config.get_delay(2)
    
    assert delay_0 == 0.5, f"Délai 0 devrait être 0.5, got {delay_0}"
    assert delay_1 == 1.0, f"Délai 1 devrait être 1.0, got {delay_1}"
    assert delay_2 == 2.0, f"Délai 2 devrait être 2.0, got {delay_2}"
    
    print(f"✅ Délais corrects: {delay_0}s → {delay_1}s → {delay_2}s")
    print()


async def test_exceptions():
    """Tester les exceptions personnalisées."""
    print("🧪 Test 3: Custom Exceptions")
    print("=" * 60)
    
    try:
        raise AIServiceException("EurIA API timeout")
    except AIServiceException as e:
        assert "indisponible" in e.detail
        print(f"✅ AIServiceException: {e.detail}")
    
    try:
        raise DiscogsServiceException("Connection refused")
    except DiscogsServiceException as e:
        assert "indisponible" in e.detail
        print(f"✅ DiscogsServiceException: {e.detail}")
    
    print()


def test_retry_decorator():
    """Tester le décorateur retry."""
    print("🧪 Test 4: Retry Decorator")
    print("=" * 60)
    
    from app.core.retry import retry_with_backoff
    
    call_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Network error")
        return "success"
    
    result = flaky_function()
    assert result == "success"
    assert call_count == 2
    print(f"✅ Retry decorator: {call_count} tentatives pour succès")
    print()


def main():
    """Exécuter tous les tests."""
    print("\n" + "=" * 60)
    print("🛡️ TESTS DE ROBUSTESSE")
    print("=" * 60)
    
    try:
        test_circuit_breaker()
        test_retry_config()
        asyncio.run(test_exceptions())
        test_retry_decorator()
        
        print("=" * 60)
        print("✅ TOUS LES TESTS PASSENT")
        print("=" * 60 + "\n")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
