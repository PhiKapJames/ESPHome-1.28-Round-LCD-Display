#!/usr/bin/env python3
"""Heuristic privacy check; never a guarantee that arbitrary code is non-sensitive.
"""
from pathlib import Path
import ipaddress, re, sys
ROOT=Path(__file__).resolve().parents[1]
IGNORE={'.git','.esphome','.pio','.venv','__pycache__'}
ALLOWED_TOP={'README.md','LICENSE','CHANGELOG.md','.gitignore','.github','docs','examples','hardware',
             'packages','profiles','scripts','tests'}
errors=[]
for path in sorted(ROOT.rglob('*')):
    rel=path.relative_to(ROOT)
    if path.name=='.DS_Store' or any(p in IGNORE for p in rel.parts): continue
    if rel.parts[0] not in ALLOWED_TOP: errors.append(f'Unapproved top-level path: {rel}')
    if path.is_symlink(): errors.append(f'Symlink is not publishable: {rel}'); continue
    if not path.is_file(): continue
    if path.suffix.lower() in {'.bin','.elf','.jpg','.jpeg','.png','.webp','.ttf','.otf','.woff','.zip','.log'}:
        errors.append(f'Private/binary artifact type: {rel}'); continue
    if path.name in {'secrets.yaml','secrets.yml','.env'}: errors.append(f'Secret file: {rel}')
    try: text=path.read_text(encoding='utf-8')
    except UnicodeDecodeError: errors.append(f'Non-text file: {rel}'); continue
    for ip in re.findall(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])',text):
        try:
            addr=ipaddress.ip_address(ip)
            if addr.is_private and not addr.is_loopback:
                errors.append(f'Non-public IP literal in {rel}')
        except ValueError: pass
    if re.search(r'(?i)\b(?:ghp_|github_pat_|sk-proj-)[A-Za-z0-9_]{15,}',text):
        errors.append(f'Credential-like token in {rel}')
    if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',text):
        errors.append(f'Private key in {rel}')
    if path.suffix in {'.yaml','.yml'}:
        for line in text.splitlines():
            m=re.match(r'^\s*(?:entity_id|page_entity|camera_entity|camera_person_entity|camera_vehicle_entity|trigger_entity):\s*(\S+)',line)
            if m:
                val=m.group(1).strip('"\'')
                if not val.startswith('${') and not re.match(r'(?:sensor|camera|binary_sensor)\.example_',val):
                    errors.append(f'Non-placeholder HA entity in {rel}')
        if 'packages' in rel.parts or 'profiles' in rel.parts or 'hardware' in rel.parts:
            if '!secret' in text: errors.append(f'Secret lookup in remote package: {rel}')
if errors:
    print('\n'.join(sorted(set(errors))),file=sys.stderr)
    sys.exit(1)
print('PASS public-source heuristics: no private addresses/entities, secret files, or image/build artifacts')
