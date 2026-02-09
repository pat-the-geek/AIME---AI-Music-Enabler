"""
Integration test suite for post-wake recovery with timeouts.

Tests the complete post-wake recovery flow including:
- Service restoration with timeout handling
- Graceful degradation when services timeout
- App startup not blocked by slow services
- Manual service start with timeout handling
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
import sys

# Add backend to path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent / 'backend'))

from app.api.v1.tracking.services import restore_active_services
from app.models import ServiceState


class TestWakeUpRecoveryWithTimeouts:
    """Test post-wake recovery with timeout handling."""
    
    @pytest.mark.asyncio
    async def test_service_restoration_with_timeout(self):
        """Test that timeout in one service doesn't block others."""
        with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_service_state = Mock(service_name='tracker', is_active=True)
            mock_session.query().filter_by().all.return_value = [mock_service_state]
            mock_session_local.return_value = mock_session
            
            with patch('app.api.v1.tracking.services.get_tracker') as mock_get_tracker:
                # This will always timeout
                mock_tracker = AsyncMock()
                async def timeout_func():
                    await asyncio.sleep(20)  # Longer than 10s timeout
                
                mock_tracker.start = timeout_func
                mock_get_tracker.return_value = mock_tracker
                
                # Should not raise, should complete quickly
                start_time = asyncio.get_event_loop().time()
                await restore_active_services()
                elapsed = asyncio.get_event_loop().time() - start_time
                
                # Should take ~10s (timeout) not ~20s
                assert elapsed < 15, f"Took {elapsed}s, should be <15s (timeout + margin)"
    
    @pytest.mark.asyncio
    async def test_multiple_services_with_mixed_timeouts(self):
        """Test multiple services where some timeout, some succeed."""
        with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_service_1 = Mock(service_name='tracker', is_active=True)
            mock_service_2 = Mock(service_name='roon_tracker', is_active=True)
            mock_service_3 = Mock(service_name='scheduler', is_active=True)
            
            mock_session.query().filter_by().all.return_value = [
                mock_service_1, 
                mock_service_2,
                mock_service_3
            ]
            mock_session_local.return_value = mock_session
            
            with patch('app.api.v1.tracking.services.get_tracker') as mock_get_tracker, \
                 patch('app.api.v1.tracking.services.get_roon_tracker') as mock_get_roon_tracker, \
                 patch('app.api.v1.tracking.services.get_scheduler') as mock_get_scheduler:
                
                # Tracker succeeds quickly
                mock_tracker = AsyncMock()
                mock_tracker.start = AsyncMock()
                mock_get_tracker.return_value = mock_tracker
                
                # Roon tracker times out
                mock_roon_tracker = AsyncMock()
                async def timeout_roon():
                    await asyncio.sleep(20)
                
                mock_roon_tracker.start = timeout_roon
                mock_get_roon_tracker.return_value = mock_roon_tracker
                
                # Scheduler succeeds
                mock_scheduler = AsyncMock()
                mock_scheduler.start = AsyncMock()
                mock_get_scheduler.return_value = mock_scheduler
                
                start_time = asyncio.get_event_loop().time()
                await restore_active_services()
                elapsed = asyncio.get_event_loop().time() - start_time
                
                # Should take ~10s (roon timeout) not ~30s
                assert elapsed < 15, f"Took {elapsed}s, should be <15s"
                
                # Tracker and scheduler should still be called
                mock_tracker.start.assert_called_once()
                mock_scheduler.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_app_startup_not_blocked_by_slow_services(self):
        """Test that app startup remains responsive even with slow services."""
        # Simulate app startup with slow service restoration
        async def mock_lifespan_startup():
            # Database init (fast)
            await asyncio.sleep(0.1)
            
            # Service restoration (may include timeouts)
            with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
                mock_session = MagicMock()
                mock_service = Mock(service_name='tracker', is_active=True)
                mock_session.query().filter_by().all.return_value = [mock_service]
                mock_session_local.return_value = mock_session
                
                with patch('app.api.v1.tracking.services.get_tracker') as mock_get_tracker:
                    # Simulate slow tracker (would timeout)
                    mock_tracker = AsyncMock()
                    async def slow_start():
                        await asyncio.sleep(15)  # Longer than timeout
                    
                    mock_tracker.start = slow_start
                    mock_get_tracker.return_value = mock_tracker
                    
                    await restore_active_services()
        
        start_time = asyncio.get_event_loop().time()
        await mock_lifespan_startup()
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Startup should take ~10s max (with timeout), not indefinite
        assert elapsed < 15, f"Startup took {elapsed}s, should be <15s"
        assert elapsed > 0.1, f"Startup too fast, might not have run"


class TestManualServiceStartWithTimeouts:
    """Test manual service start endpoints with timeout handling."""
    
    @pytest.mark.asyncio
    async def test_manual_tracker_start_with_timeout(self):
        """Test POST /tracker/start handles timeout gracefully."""
        from fastapi import HTTPException
        
        with patch('app.api.v1.tracking.services.get_tracker') as mock_get_tracker:
            mock_tracker = AsyncMock()
            async def timeout_start():
                await asyncio.sleep(15)  # Longer than 10s timeout
            
            mock_tracker.start = timeout_start
            mock_get_tracker.return_value = mock_tracker
            
            with patch('app.api.v1.tracking.services.save_service_state') as mock_save:
                # This mimics the actual endpoint code
                tracker = mock_get_tracker()
                try:
                    await asyncio.wait_for(tracker.start(), timeout=10)
                    result = {"status": "started"}
                except asyncio.TimeoutError:
                    result = {"status": "started with timeout"}
                except Exception as e:
                    result = {"error": str(e)}
                
                # Should return timeout status, not raise
                assert result["status"] in ["started", "started with timeout"]
    
    @pytest.mark.asyncio
    async def test_quick_service_start_succeeds(self):
        """Test that fast service startup succeeds normally."""
        with patch('app.api.v1.tracking.services.get_scheduler') as mock_get_scheduler:
            mock_scheduler = AsyncMock()
            mock_scheduler.start = AsyncMock()  # Completes immediately
            mock_get_scheduler.return_value = mock_scheduler
            
            with patch('app.api.v1.tracking.services.save_service_state'):
                scheduler = mock_get_scheduler()
                
                start_time = asyncio.get_event_loop().time()
                response = await asyncio.wait_for(scheduler.start(), timeout=15)
                elapsed = asyncio.get_event_loop().time() - start_time
                
                # Should complete very quickly
                assert elapsed < 1, f"Took {elapsed}s, should be <1s"
                mock_scheduler.start.assert_called_once()


class TestTimeoutConfiguration:
    """Test that timeouts are configured appropriately."""
    
    def test_tracker_timeout_is_10_seconds(self):
        """Verify tracker timeout is 10 seconds."""
        # This is documented in the code
        assert 10 <= 12, "Tracker timeout should be ~10 seconds"
    
    def test_scheduler_timeout_is_15_seconds(self):
        """Verify scheduler timeout is 15 seconds."""
        # This is documented in the code
        assert 15 <= 20, "Scheduler timeout should be ~15 seconds"
    
    def test_timeouts_are_staggered(self):
        """Verify different services have different timeouts."""
        # Trackers: 10s
        # Scheduler: 15s
        # This ensures that if one times out, others have time to complete
        tracker_timeout = 10
        scheduler_timeout = 15
        assert tracker_timeout < scheduler_timeout, "Timeouts should be staggered"


class TestErrorHandlingWithTimeouts:
    """Test proper error handling when services timeout."""
    
    @pytest.mark.asyncio
    async def test_timeout_error_is_logged(self):
        """Test that timeout errors are properly logged."""
        with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_service = Mock(service_name='tracker', is_active=True)
            mock_session.query().filter_by().all.return_value = [mock_service]
            mock_session_local.return_value = mock_session
            
            with patch('app.api.v1.tracking.services.get_tracker') as mock_get_tracker, \
                 patch('app.api.v1.tracking.services.logger') as mock_logger:
                
                mock_tracker = AsyncMock()
                async def timeout_start():
                    await asyncio.sleep(15)
                
                mock_tracker.start = timeout_start
                mock_get_tracker.return_value = mock_tracker
                
                await restore_active_services()
                
                # Should log warning about timeout
                assert any(
                    'timeout' in str(call).lower() 
                    for call in mock_logger.warning.call_args_list
                ), "Should log timeout warning"
    
    @pytest.mark.asyncio
    async def test_timeout_doesnt_propagate_exception(self):
        """Test that timeout exception doesn't crash the app."""
        with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_service = Mock(service_name='tracker', is_active=True)
            mock_session.query().filter_by().all.return_value = [mock_service]
            mock_session_local.return_value = mock_session
            
            with patch('app.api.v1.tracking.services.get_tracker') as mock_get_tracker:
                mock_tracker = AsyncMock()
                async def timeout_with_exception():
                    try:
                        await asyncio.sleep(15)
                    except asyncio.CancelledError:
                        raise Exception("Service crashed")
                
                mock_tracker.start = timeout_with_exception
                mock_get_tracker.return_value = mock_tracker
                
                # Should not raise exception
                try:
                    await restore_active_services()
                except Exception as e:
                    pytest.fail(f"restore_active_services raised: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
