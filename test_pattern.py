#!/usr/bin/env python3

import re

patterns = [
    r'(?i)(password|passwd|pwd)\s*[:=]\s*[^\s"\']{8,}',
]

content = 'password=secret123456789'
print(f'Content: {content}')

for pattern in patterns:
    matches = re.findall(pattern, content)
    if matches:
        print(f'MATCHED: {pattern}')
        print(f'  Matches: {matches}')
    else:
        print(f'No match: {pattern}')
        
# Test simple case
simple_pattern = r'password\s*=\s*\w{8,}'
matches = re.findall(simple_pattern, content)
print(f'\nSimple pattern: {simple_pattern}')
print(f'Matches: {matches}')