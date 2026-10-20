"""Apply a JSON of tactic edits to TACTIC.md files.
Usage: python3 Workflow/Tools/tactics/apply_polish.py EDITS.json
EDITS maps "<library>/<slug>" to {"pick": str, "role": str (titles-thumbnails only), "fields": {what|why|how|when|check: str}}.
- pick  → a "**Pick:** …" line right after the header line (replaced if present)
- role  → "role: <role>" inserted into the header line after the library tag (replaced if present)
- fields → replaces the whole field paragraph(s) up to the next bold label
Keys starting with "_" are ignored. Then rebuild the index with build_index.py."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'Tactics'
LABEL = {'what': 'What', 'why': 'Why it works', 'how': 'How we apply it', 'when': 'Use when / skip when', 'check': 'Check'}
NEXT = r'(?=\n\*\*(?:What|Why it works|How we apply it|Use when / skip when|Check|Related|Examples|Sources?)\b)'

edits = json.loads(Path(sys.argv[1]).read_text())
done = 0
for key, e in edits.items():
    if key.startswith('_'):
        continue
    md = ROOT / key / 'TACTIC.md'
    if not md.exists():
        print('missing', key); continue
    lines = md.read_text().split('\n')
    head = 2  # line 3 is the header: `lib` · stages: … · status: … · source: …
    assert lines[head].startswith('`'), (key, lines[head])
    if e.get('role'):
        lines[head] = re.sub(r' · role: [a-z]+', '', lines[head])
        lines[head] = re.sub(r'^(`[^`]+`)', rf'\1 · role: {e["role"]}', lines[head])
    if e.get('pick'):
        if len(lines) > head + 2 and lines[head + 2].startswith('**Pick:**'):
            lines[head + 2] = f'**Pick:** {e["pick"]}'
        else:
            lines[head + 1:head + 1] = ['', f'**Pick:** {e["pick"]}']
    txt = '\n'.join(lines)
    for f, new in (e.get('fields') or {}).items():
        lab = re.escape(LABEL[f])
        pat = re.compile(rf'\*\*{lab}:\*\* .*?' + NEXT, re.S)
        assert pat.search(txt), (key, f)
        txt = pat.sub(lambda m: f'**{LABEL[f]}:** {new}\n', txt, count=1)
    md.write_text(txt)
    done += 1
print('updated', done)
