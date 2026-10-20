#!/usr/bin/env python3
"""Load only the tactics a step needs. Stdlib only.

  tactics.py find [--format long|short] [--stage S] [--face presenter|faceless|mixed] [--mode native|cut]
                  [--core] [--text WORDS] [--lib LIB]
        one line per match: slug · pick · (stages) — search before opening anything
  tactics.py show SLUG… [--full]
        the working card: name, pick, how we apply it, use/skip, check (≈80 words); --full prints the whole TACTIC.md
  tactics.py core [--format long|short] [--stage S]
        the core checks that apply every time
  tactics.py build
        rebuild the router indexes and the per-stage pick files (same as build_index.py)

Header line 3 of a TACTIC.md:
  `<lib>` · formats: … · [role: … ·] [face: … ·] [mode: … ·] [core: yes ·] stages: … · status: … · source: …
Missing fields mean: formats long, face any, mode any, core no."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'Tactics'
FIELDS = ('What', 'Why it works', 'How we apply it', 'Use when / skip when', 'Check')


def parse(md):
    txt = md.read_text()
    lines = txt.splitlines()
    head = lines[2]
    meta = re.search(r'stages: ([^·\n]+) · status: ([^·\n]+?)\s*(?:·|$)', head)
    if not meta:
        raise SystemExit(f'{md}: line 3 must read "`<library>` · … stages: … · status: … · source: …"')
    def tag(name, default=''):
        m = re.search(rf'· {name}: ([a-z, -]+?) ·', head)
        return m.group(1).strip() if m else default
    fields = {}
    for f in FIELDS:
        m = re.search(rf'\*\*{re.escape(f)}:\*\* (.*?)(?=\n\*\*[A-Z][^*]*:\*\*|\n## |\Z)', txt, re.S)
        fields[f] = m.group(1).strip() if m else ''
    pick = re.search(r'^\*\*Pick:\*\* (.+)$', txt, re.M)
    return dict(lib=md.parent.parent.name, slug=md.parent.name, path=md, name=lines[0].lstrip('# ').strip(),
                stages=[s.strip() for s in meta.group(1).split(',') if s.strip()], status=meta.group(2).strip(),
                formats={f.strip() for f in tag('formats', 'long').split(',')}, role=tag('role'),
                face={f.strip() for f in tag('face', 'any').split(',')}, mode={f.strip() for f in tag('mode', 'any').split(',')},
                core=tag('core') == 'yes', pick=(pick.group(1) if pick else fields['What'][:120]).replace('|', '/'),
                fields=fields, text=txt)


def load():
    return [parse(md) for md in sorted(ROOT.glob('*/*/TACTIC.md'))]


def matches(t, a):
    if a.get('format') and a['format'] not in t['formats']:
        return False
    if a.get('lib') and t['lib'] != a['lib']:
        return False
    if a.get('stage') and a['stage'] not in t['stages']:
        return False
    if a.get('face') and not ({'any', a['face']} & t['face']):
        return False
    if a.get('mode') and not ({'any', 'both', a['mode']} & t['mode']):
        return False
    if a.get('core') and not t['core']:
        return False
    if a.get('text'):
        hay = (t['name'] + ' ' + t['pick'] + ' ' + t['fields']['What']).lower()
        if not all(w.lower() in hay for w in a['text'].split()):
            return False
    return True


def args(argv):
    out, i = {}, 0
    while i < len(argv):
        k = argv[i]
        if k in ('--core', '--full'):
            out[k[2:]] = True; i += 1
        elif k.startswith('--'):
            out[k[2:]] = argv[i + 1]; i += 2
        else:
            out.setdefault('slugs', []).append(k); i += 1
    return out


def main():
    cmd, a = (sys.argv[1] if len(sys.argv) > 1 else 'help'), args(sys.argv[2:])
    if cmd == 'build':
        import runpy
        runpy.run_path(str(Path(__file__).with_name('build_index.py')), run_name='__main__'); return 0
    ts = load()
    if cmd in ('find', 'core'):
        if cmd == 'core':
            a['core'] = True
        hits = [t for t in ts if matches(t, a)]
        for t in hits:
            badge = '' if t['status'] == 'candidate' else f' [{t["status"]}]'
            print(f"{t['lib']}/{t['slug']}{badge} · {t['pick']} · ({', '.join(t['stages'])})")
        print(f'-- {len(hits)} of {len(ts)}; open with: tactics.py show <slug>', file=sys.stderr)
        return 0
    if cmd == 'show':
        for s in a.get('slugs', []):
            t = next((t for t in ts if t['slug'] == s or f"{t['lib']}/{t['slug']}" == s), None)
            if not t:
                print(f'no tactic {s}'); continue
            if a.get('full'):
                print(t['text']); continue
            print(f"## {t['name']}  ({t['lib']}/{t['slug']}; {', '.join(sorted(t['formats']))}; {t['status']})")
            print(f"Pick: {t['pick']}")
            for f in ('How we apply it', 'Use when / skip when', 'Check'):
                print(f"{f}: {t['fields'][f]}")
            print(f"Examples and sources: {t['path'].relative_to(ROOT.parent.parent)} (use --full)\n")
        return 0
    print(__doc__); return 0


if __name__ == '__main__':
    sys.exit(main())
