#!/usr/bin/env python3
"""Test script for Roon control functionality."""
import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.core.config import get_settings
from app.services.roon_service import RoonService

settings = get_settings()
roon_server = settings.app_config.get('roon_server')
roon_token = settings.app_config.get('roon_token')

print(f"🔧 Testing Roon Control")
print(f"  Server: {roon_server}")
print(f"  Token: {roon_token[:20]}...")

roon_service = RoonService(server=roon_server, token=roon_token)

zones = roon_service.get_zones()
zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
print(f"\n📡 Available zones ({len(zones)}):")
for name in zone_names:
    print(f"   - {name}")

# Try to find a zone ID
first_zone_id = list(zones.keys())[0] if zones else None
if first_zone_id:
    zone_info = zones[first_zone_id]
    zone_name = zone_info.get('display_name', 'Unknown')
    print(f"\n🎮 Testing with zone: {zone_name}")
    print(f"   ID: {first_zone_id}")
    print(f"   Current state: {zone_info.get('state', 'unknown')}")
    
    # Try pause control
    print(f"\n   Sending 'pause' command...")
    result = roon_service.playback_control(first_zone_id, "pause")
    print(f"   Result: {result}")
    
    # Check zone state
    zones_after = roon_service.get_zones()
    zone_after = zones_after.get(first_zone_id, {})
    print(f"   State after pause: {zone_after.get('state', 'unknown')}")
else:
    print("❌ No zones found!")
