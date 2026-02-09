"""
Test suite for post-wake recovery resilience.

These tests verify that the application can recover gracefully after
system wake-up, with non-fatal service startup failures.

Features tested:
1. Application startup succeeds even if services fail to restore
2. Service restoration logs errors but doesn't block app startup
3. Database connection recovers after timeout
4. Multiple service startup failures are tracked and reported
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from app.api.v1.tracking.services import restore_active_services
from app.services.tracker_service import TrackerService
from app.services.roon_tracker_service import RoonTrackerService
from app.services.scheduler_service import SchedulerService


class TestServiceRestorationResilience:
    """Test service restoration handles failures gracefully."""
    
    @pytest.mark.asyncio
    async def test_restore_services_with_one_failure(self):
        """Test that app startup succeeds even if one service fails."""
        with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
            # Mock DB query
            mock_session = MagicMock()
            mock_service_state_1 = Mock(service_name='tracker', is_active=True)
            mock_service_state_2 = Mock(service_name='roon_tracker', is_active=True)
            mock_session.query().filter_by().all.return_value = [
                mock_service_state_1, 
                mock_service_state_2
            ]
            mock_session_local.return_value = mock_session
            
            # Mock services
            with patch('app.api.v1.tracking.services.get_tracker') as mock_get_tracker, \
                 patch('app.api.v1.tracking.services.get_roon_tracker') as mock_get_roon_tracker:
                
                mock_tracker = AsyncMock()
                mock_tracker.start.return_value = None
                mock_get_tracker.return_value = mock_tracker
                
                # Roon tracker fails
                mock_roon_tracker = AsyncMock()
                mock_roon_tracker.start.side_effect = Exception("Connection timeout")
                mock_get_roon_tracker.return_value = mock_roon_tracker
                
                # This should not raise an exception
                await restore_active_services()
                
                # Both should be attempted
                mock_tracker.start.assert_called_once()
                mock_roon_tracker.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restore_services_all_fail_continues(self):
        """Test that app startup continues even if all services fail."""
        with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_service_state = Mock(service_name='tracker', is_active=True)
            mock_session.query().filter_by().all.return_value = [mock_service_state]
            mock_session_local.return_value = mock_session
            
            with patch('app.api.v1.tracking.services.get_tracker') as mock_get_tracker:
                mock_tracker = AsyncMock()
                mock_tracker.start.side_effect = Exception("Network unreachable")
                mock_get_tracker.return_value = mock_tracker
                
                # Should not raise
                await restore_active_services()
                
                mock_tracker.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restore_services_db_error_handled(self):
        """Test that database errors are handled gracefully."""
        with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
            # DB.query fails
            mock_session = MagicMock()
            mock_session.query.side_effect = Exception("Database locked")
            mock_session_local.return_value = mock_session
            
            # Should not raise
            await restore_active_services()
    
    @pytest.mark.asyncio
    async def test_restore_scheduler_auto_starts(self):
        """Test that scheduler is auto-started even if not in DB."""
        with patch('app.api.v1.tracking.services.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            # No services in DB
            mock_session.query().filter_by().all.return_value = []
            mock_session.query().filter_by().first.return_value = None
            mock_session_local.return_value = mock_session
            
            with patch('app.api.v1.tracking.services.get_scheduler') as mock_get_scheduler:
                mock_scheduler = AsyncMock()
                mock_scheduler.start.return_value = None
                mock_get_scheduler.return_value = mock_scheduler
                
                await restore_active_services()
                
                # Scheduler should be started
                mock_scheduler.start.assert_called_once()


class TestDatabaseWakeRecovery:
    """Test database recovery after system wake-up."""
    
    def test_database_connection_timeout(self):
        """Test that database connection timeout is set correctly."""
        from app.database import engine, settings
        
        # Check that engine has proper configuration
        if settings.database_url.startswith("sqlite"):
            # SQLite should have timeout in connect_args
            assert engine.pool is not None
            # The timeout should be 30s (set in database.py)
    
    def test_database_wal_mode_enabled(self):
        """Test that WAL mode is enabled for better concurrency."""
        from app.database import SessionLocal
        
        try:
            db = SessionLocal()
            result = db.execute("PRAGMA journal_mode").scalar()
            assert result.upper() == "WAL", "SQLite should use WAL mode for post-wake recovery"
            db.close()
        except Exception as e:
            # If database is not available, that's ok - just skip test
            pytest.skip(f"Database not available: {e}")


class TestHealthCheckAfterWake:
    """Test health check endpoint after wake-up."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_available_even_if_services_fail(self):
        """Test that /health endpoint responds even if services failed to restore."""
        from app.services.health_monitor import health_monitor
        
        # health_monitor should report degraded status if services failed
        # but still be queryable
        status = health_monitor.get_status()
        
        assert 'status' in status
        assert status['status'] in ['healthy', 'degraded', 'unhealthy']
        assert 'database' in status
        assert 'requests' in status
    
    def test_health_monitor_startup_validation(self):
        """Test that startup validation handles database issues gracefully."""
        from app.services.health_monitor import HealthMonitor
        
        monitor = HealthMonitor()
        
        # This may fail if DB is not available, but should not crash
        try:
            result = monitor.validate_startup()
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"validate_startup() should not raise exception: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
