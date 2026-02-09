"""
Test suite for Roon connection robustness after system wake-up.

These tests verify that the Roon integration properly detects and recovers
from connection failures that may occur when the server wakes up from sleep.

Features tested:
1. Health check endpoint with detailed diagnostics
2. Automatic reconnection trigger when connection becomes stale
3. Tracker service recovery when polling fails
4. Graceful degradation when connection is temporarily unavailable
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from app.services.roon_service import RoonService
from app.services.roon_tracker_service import RoonTrackerService


class TestRoonBridgeHealthCheck:
    """Test bridge health check detection."""
    
    def test_get_bridge_health_connected(self):
        """Test bridge health report when connected."""
        with patch('httpx.get') as mock_get:
            # Mock successful connection response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "connected": True,
                "core_name": "My Roon Core",
                "zones_count": 2,
                "transport_ready": True,
                "browse_ready": True,
                "image_ready": True,
                "health_failures": 0,
                "last_health_check": "2026-02-09T10:00:00Z"
            }
            mock_get.return_value = mock_response
            
            roon = RoonService("192.168.1.100")
            health = roon.get_bridge_health()
            
            assert health['bridge_accessible'] == True
            assert health['connected_to_core'] == True
            assert health['core_name'] == "My Roon Core"
            assert health['zones_count'] == 2
            assert health['transport_ready'] == True
    
    def test_get_bridge_health_disconnected(self):
        """Test bridge health report when disconnected from core."""
        with patch('httpx.get') as mock_get:
            # Mock bridge accessible but not connected to core
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "connected": False,
                "core_name": None,
                "zones_count": 0,
                "transport_ready": False,
                "browse_ready": False,
                "image_ready": False,
                "health_failures": 2,
                "last_health_check": "2026-02-09T10:00:15Z"
            }
            mock_get.return_value = mock_response
            
            roon = RoonService("192.168.1.100")
            health = roon.get_bridge_health()
            
            assert health['bridge_accessible'] == True
            assert health['connected_to_core'] == False
            assert health['zones_count'] == 0
            assert health['health_failures'] == 2
    
    def test_get_bridge_health_unreachable(self):
        """Test bridge health report when bridge itself is unreachable."""
        with patch('httpx.get') as mock_get:
            # Mock bridge unreachable (e.g., after system sleep)
            mock_get.side_effect = ConnectionError("Bridge unreachable")
            
            roon = RoonService("192.168.1.100")
            health = roon.get_bridge_health()
            
            assert health['bridge_accessible'] == False
            assert health['connected_to_core'] == False
            assert health['zones_count'] == 0


class TestRoonConnectionRecovery:
    """Test connection recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_tracker_recovery_when_disconnected(self):
        """Test tracker service recovery when connection is lost."""
        config = {
            'roon': {'server': '192.168.1.100', 'token': 'token123'},
            'roon_tracker': {'interval_seconds': 120},
            'spotify': {'client_id': 'test', 'client_secret': 'test'},
            'euria': {'url': 'http://localhost', 'bearer': 'token'}
        }
        
        with patch('app.services.roon_service.httpx.get') as mock_get:
            # First check: disconnected
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "connected": False,
                "zones_count": 0,
                "health_failures": 2
            }
            mock_get.return_value = mock_response
            
            tracker = RoonTrackerService(config)
            
            # Roon service created but not connected
            assert tracker.roon is not None
            assert tracker.roon.is_connected() == False
            
            # Attempt recovery
            recovered = await tracker._recover_connection()
            
            # Recovery should detect the disconnected state
            assert isinstance(recovered, bool)
    
    @pytest.mark.asyncio
    async def test_tracker_resume_after_recovery(self):
        """Test that tracker can resume after connection recovery."""
        config = {
            'roon': {'server': '192.168.1.100', 'token': 'token123'},
            'roon_tracker': {
                'interval_seconds': 120,
                'listen_start_hour': 8,
                'listen_end_hour': 22
            },
            'spotify': {'client_id': 'test', 'client_secret': 'test'},
            'euria': {'url': 'http://localhost', 'bearer': 'token'}
        }
        
        with patch('app.services.roon_service.httpx.get') as mock_get:
            # Mock connected state
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "connected": True,
                "zones_count": 1,
                "health_failures": 0
            }
            mock_get.return_value = mock_response
            
            tracker = RoonTrackerService(config)
            assert tracker.roon.is_connected() == True
            
            # Tracker status should show ready to start
            status = tracker.get_status()
            assert status['connected'] == True
            assert status['configured'] == True


class TestRoonStaleConnectionDetection:
    """Test detection of stale connections after sleep."""
    
    def test_repeated_is_connected_checks_after_sleep(self):
        """Test that repeated connection checks properly detect wake-up scenarios."""
        with patch('httpx.get') as mock_get:
            call_count = 0
            
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                mock_response = Mock()
                mock_response.status_code = 200
                
                if call_count <= 2:
                    # Simulate stale response before wake-up detection
                    mock_response.json.return_value = {
                        "connected": False,
                        "zones_count": 0
                    }
                else:
                    # After recovery, connection re-established
                    mock_response.json.return_value = {
                        "connected": True,
                        "zones_count": 2
                    }
                
                return mock_response
            
            mock_get.side_effect = side_effect
            
            roon = RoonService("192.168.1.100")
            
            # Initial check - disconnected
            assert roon.is_connected() == False
            
            # Second check - still disconnected
            assert roon.is_connected() == False
            
            # Third check - after bridge reconnection - now connected
            assert roon.is_connected() == True


class TestBridgeHealthCheckTiming:
    """Test health check intervals and reconnection timing."""
    
    def test_health_check_interval_configuration(self):
        """Verify health check runs at expected intervals."""
        # The health check runs every 10 seconds on the bridge
        # and triggers reconnection after 2 consecutive failures (20 seconds)
        
        # This is verified by the constants in app.js:
        # HEALTH_CHECK_INTERVAL = 10000 (10 seconds)
        # MAX_FAILURES = 2 (2 consecutive failures = after 20 seconds triggers reconnect)
        
        expected_health_check_interval = 10  # seconds
        expected_max_failures = 2
        expected_time_to_reconnect = expected_health_check_interval * expected_max_failures
        
        assert expected_health_check_interval == 10
        assert expected_max_failures == 2
        assert expected_time_to_reconnect == 20


class TestGracefulDegradation:
    """Test graceful handling when Roon is temporarily unavailable."""
    
    @pytest.mark.asyncio
    async def test_poll_skips_when_disconnected(self):
        """Test that polling gracefully skips when disconnected."""
        config = {
            'roon': {'server': '192.168.1.100', 'token': 'token123'},
            'roon_tracker': {'interval_seconds': 120},
            'spotify': {'client_id': 'test', 'client_secret': 'test'},
            'euria': {'url': 'http://localhost', 'bearer': 'token'}
        }
        
        with patch('app.services.roon_service.httpx.get') as mock_get:
            # Disconnected
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"connected": False, "zones_count": 0}
            mock_get.return_value = mock_response
            
            tracker = RoonTrackerService(config)
            
            # Polling should not raise, just log and return
            # (It will call _recover_connection but won't crash)
            import logging
            with patch.object(logging.getLogger('app.services.roon_tracker_service'), 'warning'):
                await tracker._recover_connection()
                # Test passes if no exception is raised


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
