"""Utility pour retry logic et circuit breaker."""

import asyncio
import time
import logging
from typing import TypeVar, Callable, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
import httpx

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration pour la stratégie de retry."""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculer le délai pour une tentative."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay


class CircuitBreaker:
    """Circuit breaker pour éviter de surcharger les services."""
    
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        recovery_timeout: int = 300
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
    
    def record_success(self):
        """Enregistrer un succès."""
        if self.state == "HALF_OPEN":
            self.success_count += 1
            logger.info(f"✅ {self.service_name} succès ({self.success_count}/{self.success_threshold})")
            
            if self.success_count >= self.success_threshold:
                self._close()
        elif self.state == "CLOSED":
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Enregistrer une failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            self._open()
        elif self.state == "HALF_OPEN":
            self._open()
        
        logger.warning(f"❌ {self.service_name} failure ({self.failure_count}/{self.failure_threshold})")
    
    def _open(self):
        """Ouvrir le circuit breaker."""
        self.state = "OPEN"
        self.opened_at = datetime.now()
        self.failure_count = 0
        self.success_count = 0
        logger.error(f"🔴 Circuit breaker OUVERT pour {self.service_name}")
    
    def _close(self):
        """Fermer le circuit breaker."""
        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        logger.info(f"🟢 Circuit breaker FERMÉ pour {self.service_name}")
    
    def _half_open(self):
        """Mettre en HALF_OPEN pour permettre une tentative."""
        self.state = "HALF_OPEN"
        self.success_count = 0
        logger.info(f"🟡 Circuit breaker DEMI-OUVERT pour {self.service_name}")
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Exécuter une fonction avec circuit breaker."""
        if self.state == "OPEN":
            # Vérifier si on peut passer en HALF_OPEN
            if self.opened_at and datetime.now() > self.opened_at + timedelta(seconds=self.recovery_timeout):
                self._half_open()
            else:
                from app.core.exceptions import CircuitBreakerOpen
                raise CircuitBreakerOpen(self.service_name, self.recovery_timeout)
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
    
    async def call_async(self, func: Callable[..., Any], *args, **kwargs) -> T:
        """Exécuter une fonction async avec circuit breaker."""
        if self.state == "OPEN":
            # Vérifier si on peut passer en HALF_OPEN
            if self.opened_at and datetime.now() > self.opened_at + timedelta(seconds=self.recovery_timeout):
                self._half_open()
            else:
                from app.core.exceptions import CircuitBreakerOpen
                raise CircuitBreakerOpen(self.service_name, self.recovery_timeout)
        
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[type]] = None
):
    """Décorateur pour retry logic avec backoff exponentiel."""
    
    if retryable_exceptions is None:
        retryable_exceptions = [
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.RemoteProtocolError,
            asyncio.TimeoutError,
            ConnectionError,
            TimeoutError
        ]
    
    config = RetryConfig(max_attempts, initial_delay, max_delay, exponential_base, jitter)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Vérifier si c'est une exception retry-able
                    is_retryable = any(isinstance(e, exc_type) for exc_type in retryable_exceptions)
                    
                    if not is_retryable or attempt == max_attempts - 1:
                        raise
                    
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"⚠️ Tentative {attempt + 1}/{max_attempts} échouée: {e}. "
                        f"Nouvelle tentative dans {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
            
            if last_exception:
                raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Vérifier si c'est une exception retry-able
                    is_retryable = any(isinstance(e, exc_type) for exc_type in retryable_exceptions)
                    
                    if not is_retryable or attempt == max_attempts - 1:
                        raise
                    
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"⚠️ Tentative {attempt + 1}/{max_attempts} échouée: {e}. "
                        f"Nouvelle tentative dans {delay:.2f}s..."
                    )
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
        
        # Déterminer si la fonction est async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
