#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/herb/Desktop/GitUp')

from pathlib import Path
from gitup.core.risk_mitigation import SecurityRiskDetector
import os
import fnmatch

os.chdir('/home/herb/Desktop/GitUp/test_symlinks')

detector = SecurityRiskDetector(Path('.'))

# Test the _scan_symbolic_link method directly
file_path = Path('.env_link')

print(f'=== Testing {file_path} ===')
print(f'is_symlink: {file_path.is_symlink()}')
print(f'exists: {file_path.exists()}')

if file_path.is_symlink():
    target = os.readlink(file_path)
    print(f'target: {target}')
    
    # Test the _scan_symbolic_link method directly
    print(f'\nCalling _scan_symbolic_link directly:')
    risks = detector._scan_symbolic_link(file_path)
    print(f'Direct call risks: {len(risks)}')
    for risk in risks:
        print(f'  - {risk.risk_type.value}: {risk.description}')
    
    # Test full _scan_file method
    print(f'\nCalling _scan_file:')
    all_risks = detector._scan_file(file_path)
    print(f'Full scan risks: {len(all_risks)}')
    for risk in all_risks:
        print(f'  - {risk.risk_type.value}: {risk.description}')