#!/usr/bin/env python3
"""Test scheduler output generation"""
import sys
import os
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models.models import Album
from datetime import datetime

db = SessionLocal()
albums = db.query(Album).all()
print(f'✅ Total albums in DB: {len(albums)}')

# Test path calculation
file_path = os.path.abspath('backend/app/services/scheduler_service.py')
print(f'File path: {file_path}')

current_dir = file_path
for i in range(4):
    current_dir = os.path.dirname(current_dir)
    
project_root = current_dir
output_dir = os.path.join(project_root, 'Scheduled Output')
print(f'Output dir: {output_dir}')
print(f'Output dir exists: {os.path.exists(output_dir)}')

# Try to create a test file
try:
    os.makedirs(output_dir, exist_ok=True)
    test_file = os.path.join(output_dir, 'test.txt')
    with open(test_file, 'w') as f:
        f.write('test')
    print(f'✅ Created test file: {test_file}')
    os.remove(test_file)
    print(f'✅ Cleaned up test file')
except Exception as e:
    print(f'❌ Error: {e}')

# List files in output dir
print(f'\n📁 Files in Scheduled Output:')
if os.path.exists(output_dir):
    files = os.listdir(output_dir)
    if files:
        for f in files:
            filepath = os.path.join(output_dir, f)
            size = os.path.getsize(filepath)
            print(f'  - {f} ({size} bytes)')
    else:
        print('  (empty)')
