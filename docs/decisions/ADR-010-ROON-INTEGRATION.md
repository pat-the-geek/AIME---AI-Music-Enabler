# ADR-010: Roon Integration Architecture

**Status**: ✅ Accepted  
**Date**: 2026-02-07  
**Priority**: Medium  
**Author**: Engineering Team  
**Reviewers**: Architecture Committee  

## 1. Context

Roon is a premium music server platform with complex metadata and zone management:

### 1.1 Roon Complexity

**Data Structures**:
- Zones: Multiple playback endpoints (kitchen, office, car)
- Queue: Current track, history, favorites
- Library: Local storage, TIDAL integration, streaming services
- Metadata: Albums, artists, genres with Roon's enhancements

**Real-time Updates**:
- Playback status changes (play, pause, next)
- Add track to queue
- Zone switching
- Volume control

**Authentication**:
- Roon Core discovery via network broadcast
- Token-based authentication
- Session management across disconnects

### 1.2 Current Challenges

1. **Network Discovery**
   - Roon Core not at fixed IP (DHCP changes)
   - May go offline (update, power loss)
   - Multiple cores on same network

2. **Real-time Synchronization**
   - Library changes happen outside AIME
   - Metadata enhancements in Roon
   - Need to sync without constant polling

3. **Performance**
   - Large libraries (100k+ tracks)
   - Metadata enrichment expensive
   - Caching decisions complex

4. **Error Handling**
   - Network timeouts common
   - Failed operations need clear error messages
   - Recovery without user intervention

**Problem**: How to integrate with Roon reliably while handling network issues, real-time updates, and large data volumes?

## 2. Decision

We adopt **Roon as optional integration** with **automatic discovery**, **request-response pattern** (no subscriptions), and **graceful degradation**.

### 2.1 Roon Integration Architecture

```python
# Pattern: backend/app/services/roon_service.py

from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RoonServiceException(Exception):
    """Base exception for Roon service errors."""
    pass

class RoonNotFound(RoonServiceException):
    """Roon Core not discovered."""
    pass

class RoonAuthFailed(RoonServiceException):
    """Authentication with Roon Core failed."""
    pass

class RoonService:
    """
    Roon Core integration.
    
    Features:
    - Automatic Core discovery (broadcast)
    - Library browsing & querying
    - Playback control (limited)
    - Metadata enrichment
    - Optional graceful degradation
    """
    
    def __init__(self, core_ip: str = None, token: str = None, enabled: bool = False):
        """
        Initialize Roon service.
        
        Args:
            core_ip: IP address of Roon Core (auto-discover if None)
            token: Authentication token (obtained during first pairing)
            enabled: Whether to enable Roon integration
        """
        self.core_ip = core_ip
        self.token = token
        self.enabled = enabled
        self.is_authenticated = False
        self._session: Optional[RoonCoreConnection] = None
        self._cache = {}
    
    async def discover_core(self) -> str:
        """
        Discover Roon Core on network via broadcast.
        
        Returns:
            IP address of Roon Core
            
        Raises:
            RoonNotFound: If no Core found on network
        """
        if not self.enabled:
            raise RoonServiceException("Roon integration disabled")
        
        logger.info("Discovering Roon Core on network...")
        
        from roonapi import RoonApi
        import socket
        
        try:
            # Send broadcast discovery packet
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Broadcast to find Roon Core
            sock.sendto(b"RoonApi", ("255.255.255.255", 9100))
            
            # Wait for response (with timeout)
            sock.settimeout(5.0)
            data, addr = sock.recvfrom(1024)
            core_ip = addr[0]
            
            logger.info(f"✅ Found Roon Core at {core_ip}")
            return core_ip
        
        except socket.timeout:
            raise RoonNotFound("Roon Core not found on network (timeout after 5s)")
        except Exception as e:
            raise RoonNotFound(f"Roon discovery failed: {e}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Roon Core.
        
        First run: User must approve AIME in Roon UI
        Once approved: Token saved for future sessions
        
        Returns:
            True if authenticated successfully
            
        Raises:
            RoonAuthFailed: If authentication fails
        """
        if not self.enabled:
            return False
        
        if not self.core_ip:
            self.core_ip = await self.discover_core()
        
        logger.info(f"Authenticating with Roon Core at {self.core_ip}...")
        
        try:
            from roonapi import RoonApi
            
            self._session = RoonApi(
                host=self.core_ip,
                token=self.token,
                extension_id="aime"
            )
            
            await asyncio.sleep(0.5)  # Let connection establish
            
            if self._session.token:
                self.token = self._session.token  # Save for next time
                self.is_authenticated = True
                logger.info("✅ Authenticated with Roon Core")
                return True
            else:
                raise RoonAuthFailed("No token received from Core")
        
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise RoonAuthFailed(f"Auth failed: {e}")
    
    async def get_library(self) -> Dict[str, Any]:
        """
        Get user's Roon library contents.
        
        Returns:
            Dictionary with:
            - albums: List of Album dicts
            - artists: List of Artist dicts
            - tracks: List of Track dicts
            
        Raises:
            RoonServiceException: If not connected
        """
        if not self.is_authenticated:
            await self.authenticate()
        
        if not self._session:
            raise RoonServiceException("Not connected to Roon Core")
        
        logger.info("Fetching Roon library...")
        
        try:
            # Browse library (may take time for large libraries)
            library = self._session.query(
                uri="roon:browse:root",
                offset=0,
                count=10000
            )
            
            return {
                "albums": library.get("items", []),
                "count": library.get("total_count", 0)
            }
        except Exception as e:
            logger.error(f"Library fetch failed: {e}")
            raise RoonServiceException(f"Cannot fetch library: {e}")
    
    async def search_library(self, query: str) -> Dict[str, Any]:
        """
        Search Roon library.
        
        Args:
            query: Search string (artist name, album, track)
            
        Returns:
            Search results with matching items
        """
        if not self.is_authenticated:
            await self.authenticate()
        
        try:
            results = self._session.query(
                uri=f"roon:search:{query}",
                offset=0,
                count=50
            )
            
            return {
                "query": query,
                "results": results.get("items", []),
                "total_count": results.get("total_count", 0)
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"query": query, "results": [], "total_count": 0}
    
    async def add_to_zone_queue(
        self,
        zone_id: str,
        items: List[Dict[str, Any]]
    ) -> bool:
        """
        Add items to zone playback queue.
        
        Args:
            zone_id: Roon zone identifier
            items: List of album/track items to queue
            
        Returns:
            True if successful
        """
        if not self.is_authenticated:
            await self.authenticate()
        
        try:
            for item in items:
                self._session.playback_control(
                    zone_id=zone_id,
                    command="queue_next",
                    item_key=item["key"]
                )
            
            logger.info(f"Added {len(items)} items to queue")
            return True
        except Exception as e:
            logger.error(f"Queue operation failed: {e}")
            return False
    
    async def get_zones(self) -> List[Dict[str, Any]]:
        """
        Get list of available playback zones.
        
        Each zone can play music independently.
        
        Returns:
            List of zone dicts with:
            - zone_id: Unique identifier
            - display_name: User-friendly name
            - is_playing: Current playback status
            - now_playing: Current track info
        """
        if not self.is_authenticated:
            await self.authenticate()
        
        try:
            zones = self._session.query(
                uri="roon:zones"
            )
            
            return zones.get("zones", [])
        except Exception as e:
            logger.error(f"Zone query failed: {e}")
            return []
```

### 2.2 Graceful Degradation

```python
# Pattern: Continue without Roon if unavailable

async def enrich_album_with_roon(
    album: Album,
    user_id: int
) -> Album:
    """
    Enrich album with Roon metadata if available.
    
    If Roon unavailable:
    - Continue with what we have
    - Try again later
    - Don't break user workflow
    """
    
    if not roon_service.enabled:
        # Roon not configured, skip enrichment
        return album
    
    try:
        if not roon_service.is_authenticated:
            await roon_service.authenticate()
        
        # Search Roon library for album
        results = await roon_service.search_library(album.title)
        
        if results["total_count"] > 0:
            roon_item = results["results"][0]
            
            # Enrich with Roon metadata
            album.roon_key = roon_item.get("key")
            album.roon_metadata = roon_item.get("metadata", {})
            logger.info(f"✅ Enriched album with Roon metadata")
    
    except RoonNotFound:
        logger.warning("Roon Core not available, skipping enrichment")
        # Continue without Roon data
    
    except RoonAuthFailed:
        logger.warning("Roon authentication failed, retrying later")
        # Could retry with cached token next request
    
    except Exception as e:
        logger.warning(f"Roon enrichment failed: {e}")
        # Always fallback gracefully
    
    return album
```

### 2.3 API Endpoint for Roon Integration

```python
# Pattern: Routes for Roon status & control

@app.get("/api/v1/roon/status")
async def get_roon_status(
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get Roon integration status.
    
    Returns:
    {
        "enabled": true,
        "authenticated": true,
        "core_ip": "192.168.1.100",
        "zones": [
            {"zone_id": "...", "name": "Kitchen", "is_playing": false},
            {"zone_id": "...", "name": "Office", "is_playing": true}
        ]
    }
    """
    try:
        zones = await roon_service.get_zones()
        
        return {
            "enabled": roon_service.enabled,
            "authenticated": roon_service.is_authenticated,
            "core_ip": roon_service.core_ip,
            "zones": zones
        }
    except RoonNotFound:
        return {
            "enabled": roon_service.enabled,
            "authenticated": False,
            "core_ip": None,
            "error": "Roon Core not found on network",
            "zones": []
        }

@app.post("/api/v1/roon/zones/{zone_id}/queue")
async def add_to_queue(
    zone_id: str,
    items: List[Dict[str, Any]],
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Add items to Roon playback queue.
    
    Request body:
    {
        "items": [
            {"type": "album", "key": "..."},
            {"type": "track", "key": "..."}
        ]
    }
    """
    success = await roon_service.add_to_zone_queue(zone_id, items)
    
    return {
        "success": success,
        "items_added": len(items) if success else 0
    }
```

### 2.4 Testing Roon Integration

```python
# Pattern: Mock Roon Core for testing

from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_roon_service():
    """Mock Roon service for testing."""
    service = RoonService(enabled=False)  # Disabled by default
    
    # Mock methods
    service.is_authenticated = True
    service.get_zones = AsyncMock(return_value=[
        {"zone_id": "zone1", "display_name": "Kitchen", "is_playing": False},
        {"zone_id": "zone2", "display_name": "Office", "is_playing": False}
    ])
    service.search_library = AsyncMock(return_value={
        "results": [{"key": "1", "metadata": {"title": "Test Album"}}],
        "total_count": 1
    })
    service.add_to_zone_queue = AsyncMock(return_value=True)
    
    return service

@pytest.mark.asyncio
async def test_enrich_with_roon(mock_roon_service):
    """Test album enrichment with Roon metadata."""
    album = Album(title="Test Album")
    
    service = mock_roon_service
    result = await enrich_album_with_roon(album, user_id=1)
    
    # Should search Roon library
    service.search_library.assert_called_once()
    
    # Should enrich with metadata
    assert result.roon_key == "1"
    assert result.roon_metadata["title"] == "Test Album"

@pytest.mark.asyncio
async def test_roon_unavailable_degrades_gracefully(mock_roon_service):
    """If Roon unavailable, should continue without error."""
    album = Album(title="Test Album")
    
    # Disable Roon
    mock_roon_service.enabled = False
    
    result = await enrich_album_with_roon(album, user_id=1)
    
    # Should return album unchanged
    assert result.title == "Test Album"
    assert not hasattr(result, "roon_key")  # No Roon data
```

## 3. Consequences

### 3.1 ✅ Positive

1. **Optional**: Can use AIME without Roon
2. **Graceful Degradation**: Failures don't block user workflows
3. **Automatic Discovery**: No manual IP configuration needed
4. **Real-time Access**: Direct zone control for power users
5. **Metadata Enrichment**: Better searching with Roon's library

### 3.2 ⚠️ Trade-offs

1. **Network Dependency**: Roon Core must be on same network
2. **Complexity**: Extra service to manage & debug
3. **Latency**: Network calls for Roon operations
4. **Token Management**: Must save & rotate auth token

### 3.3 Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Service class | 🟡 Partial | Structure ready, API calls need testing |
| Discovery | 🟡 Partial | Broadcast logic requires roonapi library |
| Authentication | 🟡 Partial | Token storage needs integration |
| Library browsing | 🔴 TODO | Large library pagination |
| Zone control | 🔴 TODO | Queue management, playback control |
| API endpoints | 🔴 TODO | Routes for status, queue, zones |
| Testing | ✅ Done | Mock fixtures ready |

## 4. Alternatives Considered

### A. Always Require Roon
**Rejected** ❌

Make Roon mandatory for using AIME

**Why Not**: Limits user base, unnecessary for music library management

### B. Polling Roon for Updates
**Rejected** ❌

Continuously query Roon for changes

**Why Not**: High load, frequent queries, poor latency

### C. Roon Webhook Subscriptions
**Depends on Roon API** ⏳

Roon sends updates to AIME when changes occur

**Status**: Not implemented yet (Roon API limitations)
**Future**: If Roon API supports it

## 5. Implementation Plan

### Phase 4 (Completed)
- ✅ Service structure designed
- ✅ Mock fixtures created

### Phase 5 (Current - This ADR)
- 🔄 Document architecture (this ADR)
- 🔄 Implement core discovery
- 🔄 Setup authentication with token caching

### Phase 5+
- Implement library browsing
- Add zone playback control
- Build API endpoints
- Comprehensive testing

### Future (Phase 6+)
- Roon-native album queuing
- Metadata sync from Roon
- Performance optimization for large libraries

## 6. Configuration Reference

### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| ROON_ENABLED | No | false | Enable integration |
| ROON_CORE_IP | No | (auto-discover) | Core IP address |
| ROON_TOKEN | No | (obtained on first auth) | Auth token |

### Setup Procedure

1. Ensure Roon Core is running on the same network
2. Start AIME with `ROON_ENABLED=true`
3. First request to Roon will trigger auto-discovery
4. Approve AIME in Roon UI (Settings → Integrations)
5. Token saved automatically for future sessions

## 7. References

### Code Files
- [Roon service](../../backend/app/services/roon_service.py)
- [Roon API](../../backend/app/api/v1/roon.py)

### Documentation
- [ADR-004: External API Integration](./ADR-004-EXTERNAL-API-INTEGRATION.md)
- [ADR-003: Circuit Breaker](./ADR-003-CIRCUIT-BREAKER.md)

### External Resources
- [Roon API Documentation](https://github.com/TheAppgineer/roon-api)
- [Roon API Python Library](https://github.com/TheAppgineer/roon-api-python)
- [Roon Network Protocol](https://github.com/RoonLabs/node-roon-api)

### Related ADRs
- ADR-003: Circuit Breaker (timeout/failure handling)
- ADR-004: External API Integration (common patterns)
- ADR-006: Async Patterns (concurrent zone control)

## 8. Decision Trail

**Version 1.0 (2026-02-07)**: Initial decision on optional Roon integration with graceful degradation

---

**Status**: ✅ **ACCEPTED**

This design integrates Roon as an optional enhancement without impacting core AIME functionality, allowing users to opt-in to advanced zone management features.

**Next Phase**: ADR documentation complete. Transition to service layer documentation.
