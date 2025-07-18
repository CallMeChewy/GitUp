#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/herb/Desktop/GitUp')

from pathlib import Path
from gitup.core.risk_mitigation import SecurityRiskDetector
import re
import os

os.chdir('/home/herb/Desktop/GitUp/test_symlinks')

detector = SecurityRiskDetector(Path('.'))

file_path = Path('linked_secrets.txt')
relative_path = str(file_path)
stat = file_path.stat()
file_size = stat.st_size
print(f'File size: {file_size}')

# Test the actual patterns from GitUp
print(f'\nTesting GitUp credential patterns:')
content = file_path.read_text(encoding='utf-8', errors='ignore')
print(f'Content: "{content.strip()}"')

for i, pattern in enumerate(detector.credential_patterns):
    print(f'\nPattern {i+1}: {pattern}')
    matches = re.findall(pattern, content)
    if matches:
        print(f'  ✅ MATCHES: {matches}')
    else:
        print(f'  ❌ No matches')

# Test content-based risk detection directly
print(f'\n=== Testing _scan_file_content directly ===')
from datetime import datetime
last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
is_tracked = detector._is_git_tracked(file_path)
print(f'is_tracked: {is_tracked}')

content_risks = detector._scan_file_content(file_path, relative_path, file_size, last_modified, is_tracked)
print(f'Content risks found: {len(content_risks)}')
for risk in content_risks:
    print(f'  - {risk.risk_type.value}: {risk.description}')