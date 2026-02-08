#!/usr/bin/env python3
"""Test export services to verify eager loading and all albums are exported."""

from app.database import SessionLocal
from app.services.collection.export_service import ExportService
import json

def test_json_export():
    """Test JSON export includes all albums and ai_description field."""
    db = SessionLocal()
    try:
        print("🧪 Testing JSON Export Service\n")
        json_output = ExportService.export_json_full(db)
        data = json.loads(json_output)
        
        print(f"✅ JSON Export Test Results:")
        print(f"   Total albums exported: {data['total_albums']}")
        print(f"   Export date: {data['export_date']}")
        print(f"   Albums in list: {len(data['albums'])}")
        
        # Check a sample album
        if data['albums']:
            # Find an album with ai_description
            sample = None
            for album in data['albums']:
                if album.get('ai_description'):
                    sample = album
                    break
            
            if not sample:
                sample = data['albums'][0]
            
            print(f"\n📀 Sample Album:")
            print(f"   Title: {sample['title']}")
            print(f"   Artists: {sample['artists']}")
            print(f"   AI Description present: {'ai_description' in sample}")
            if sample.get('ai_description'):
                print(f"   AI Description value: {sample['ai_description'][:100]}...")
            else:
                print(f"   AI Description value: None")
            print(f"   Metadata present: {'metadata' in sample}")
            print(f"   Metadata ai_info: {sample['metadata'].get('ai_info', 'None')[:50] if sample['metadata'].get('ai_info') else 'None'}")
            print(f"   Images count: {len(sample.get('images', []))}")
        
        return data['total_albums']
    finally:
        db.close()

def test_markdown_export():
    """Test markdown export includes all albums and ai_description."""
    from app.services.markdown_export_service import MarkdownExportService
    
    db = SessionLocal()
    try:
        print("\n\n🧪 Testing Markdown Export Service\n")
        markdown = MarkdownExportService.get_collection_markdown(db)
        
        lines = markdown.split('\n')
        # Count album sections (h2 headers are album titles)
        album_count = markdown.count('\n## ')
        
        print(f"✅ Markdown Export Test Results:")
        print(f"   Total characters: {len(markdown)}")
        print(f"   Total lines: {len(lines)}")
        print(f"   Album sections detected: {album_count}")
        print(f"   Has Table of Contents: {'## Table des matières' in markdown}")
        print(f"   Has Résumé sections: {'**Résumé:**' in markdown}")
        
        # Check if md has ai_description content
        resume_count = markdown.count('**Résumé:**')
        print(f"   Résumé sections: {resume_count}")
        
        return album_count
    finally:
        db.close()

if __name__ == "__main__":
    json_count = test_json_export()
    md_count = test_markdown_export()
    
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   JSON export: {json_count} albums")
    print(f"   Markdown export: {md_count} album sections")
    print("="*60)
