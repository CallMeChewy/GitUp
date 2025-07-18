#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/herb/Desktop/GitUp')

from pathlib import Path
from gitup.core.risk_mitigation import SecurityRiskDetector

# Change to test_symlinks directory
import os
os.chdir('/home/herb/Desktop/GitUp/test_symlinks')

detector = SecurityRiskDetector(Path('.'))

# Test text file detection from within test_symlinks
for filename in ['linked_secrets.txt', 'real_secrets.txt']:
    file_path = Path(filename)
    print(f'\n=== {filename} ===')
    print(f'exists: {file_path.exists()}')
    print(f'is_symlink: {file_path.is_symlink()}')
    
    if file_path.exists():
        is_text = detector._is_text_file(file_path)
        print(f'is_text: {is_text}')
        
        # Check what's actually in the file
        with open(file_path, 'rb') as f:
            chunk = f.read(100)
            print(f'raw content: {chunk}')
            null_check = b'\0' in chunk
            print(f'has null bytes: {null_check}')
            
        # Now test full risk detection
        print(f'Testing risk detection...')
        risks = detector._scan_file(file_path)
        print(f'Risks detected: {len(risks)}')
        for risk in risks:
            print(f'  - {risk.risk_type.value}: {risk.description}')