#!/usr/bin/env python3
"""Test script to verify artist portrait markdown formatting."""

import asyncio
import httpx
import json
import sys

async def test_portrait_streaming():
    """Test the portrait streaming endpoint."""
    
    # Test with artist ID 24 (Beck)
    artist_id = 24
    url = f"http://localhost:8000/api/v1/artists/{artist_id}/article/stream"
    
    print(f"🎤 Testing portrait streaming for artist {artist_id}...")
    print(f"📡 URL: {url}\n")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    print(f"❌ Error: HTTP {response.status_code}")
                    return
                
                print(f"✅ Connected! Streaming content...\n")
                print("=" * 80)
                
                # Buffer to accumulate markdown content
                markdown_content = ""
                chunk_count = 0
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if not data_str.strip():
                            continue
                        
                        try:
                            data = json.loads(data_str)
                            
                            if data.get("type") == "metadata":
                                print(f"👤 Artist: {data.get('artist_name', 'Unknown')}")
                                print(f"💿 Albums: {data.get('albums_count', 0)}")
                                print("\n" + "=" * 80 + "\n")
                            
                            elif data.get("type") == "chunk":
                                content = data.get("content", "")
                                markdown_content += content
                                chunk_count += 1
                                
                                if chunk_count % 10 == 0:
                                    print(f"📦 {chunk_count} chunks received ({len(markdown_content)} chars)...", end="\r")
                            
                            elif data.get("type") == "done":
                                print(f"\n✅ Streaming completed! ({chunk_count} total chunks)")
                                break
                            
                            elif data.get("type") == "error":
                                print(f"\n❌ Error: {data.get('message', 'Unknown error')}")
                                return
                        
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON parse error: {e}")
                            continue
                
                print("\n" + "=" * 80)
                print("\n📝 GENERATED CONTENT (first 1500 characters):\n")
                print(markdown_content[:1500])
                
                print("\n" + "=" * 80)
                print("\n🔍 MARKDOWN FORMATTING ANALYSIS:")
                print(f"   - Total characters: {len(markdown_content)}")
                print(f"   - Contains '**' (bold): {'✅' if '**' in markdown_content else '❌'}")
                print(f"   - Contains '*' (italic): {'✅' if '*' in markdown_content else '❌'}")
                print(f"   - Contains '#' (headings): {'✅' if '#' in markdown_content else '❌'}")
                print(f"   - Contains '-' (lists): {'✅' if '-' in markdown_content else '❌'}")
                print(f"   - Contains '>' (blockquotes): {'✅' if '>' in markdown_content else '❌'}")
                
                # Check for plain text without formatting
                lines = markdown_content.split('\n')
                formatted_lines = sum(1 for line in lines if any(marker in line for marker in ['**', '*', '#', '-', '>', '1.']))
                plaintext_lines = len(lines) - formatted_lines
                
                print(f"   - Formatted lines: {formatted_lines}")
                print(f"   - Plain text lines: {plaintext_lines}")
                print(f"   - Formatting ratio: {(formatted_lines / max(len(lines), 1) * 100):.1f}%")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_portrait_streaming())
