#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/herb/Desktop/GitUp')

from pathlib import Path
from gitup.core.risk_mitigation import SecurityRiskDetector
import os

os.chdir('/home/herb/Desktop/GitUp/test_symlinks')

detector = SecurityRiskDetector(Path('.'))

# Test various symlinks
test_files = [
    'linked_secrets.txt',      # Normal name, sensitive content 
    '.env_link',               # Suspicious name (.env*)
    'system_passwords',        # Suspicious target (/etc/passwd)
    'real_secrets.txt'         # Real file for comparison
]

print('=== SYMBOLIC LINK SECURITY TEST ===\n')

for filename in test_files:
    file_path = Path(filename)
    if not file_path.exists():
        continue
        
    print(f'--- Testing {filename} ---')
    print(f'is_symlink: {file_path.is_symlink()}')
    
    if file_path.is_symlink():
        try:
            target = os.readlink(file_path)
            print(f'target: {target}')
        except:
            print(f'target: unknown')
    
    # Test risk detection
    risks = detector._scan_file(file_path)
    print(f'Risks detected: {len(risks)}')
    for risk in risks:
        print(f'  ⚠️  {risk.risk_type.value}: {risk.description}')
        print(f'      Recommendation: {risk.recommendation}')
    
    print()