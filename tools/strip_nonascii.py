# python
import re
from pathlib import Path
import sys

EMOJI_RE = re.compile(r'[^\x00-\x7F]+')

TARGETS = ['core', 'strategies', 'tools', 'app.py', 'README.md']
SUFFIXES = {'.py', '.md', '.rst', '.txt'}

changed = []

def process_file(p: Path):
    try:
        s = p.read_text(encoding='utf-8')
    except Exception as e:
        print(f"SKIP {p}: read error {e}")
        return
    new = EMOJI_RE.sub('', s)
    if new != s:
        bak = p.with_name(p.name + '.bak')
        if not bak.exists():
            bak.write_text(s, encoding='utf-8')
        p.write_text(new, encoding='utf-8')
        changed.append(p)
        print(f"STRIPPED {p}")

for t in TARGETS:
    p = Path(t)
    if p.is_file():
        if p.suffix in SUFFIXES:
            process_file(p)
        else:
            print(f"SKIP {p}: unsupported suffix")
    elif p.is_dir():
        for f in p.rglob('*'):
            if f.is_file() and f.suffix in SUFFIXES:
                process_file(f)
    else:
        print(f"NOT FOUND {p}")

print(f"TOTAL_FILES_STRIPPED={len(changed)}")
if changed:
    sys.exit(0)
else:
    sys.exit(0)