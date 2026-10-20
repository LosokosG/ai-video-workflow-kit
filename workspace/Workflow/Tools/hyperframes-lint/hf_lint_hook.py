#!/usr/bin/env python3
"""HyperFrames lint gate for Claude Code hooks (and manual/Codex use). Stdlib only.

  hf_lint_hook.py post            PostToolUse hook: stdin = hook JSON; lints the HyperFrames project of the edited file
  hf_lint_hook.py stop            Stop hook: lints projects touched this session or edited in the last 60 min
  hf_lint_hook.py check [DIR…]    manual/Codex: lint the projects containing DIR (default: cwd); exit 1 on findings

A finding blocks (exit 2 → shown to Claude, which must fix it) when it is an error, or a warning that the project
has not accepted. Accept a deliberate warning with one line in <project>/.hyperframes-lint-accept:
    <code> <elementId|*>   # why it is intentional
Errors can't be accepted. Info-level findings never block. The lint runs with the project's pinned CLI version
(`hyperframes@X` in package.json scripts), else the workspace pin (`Workflow/hyperframes-pin.txt` or $HYPERFRAMES_VERSION), else `latest`."""
import json, os, re, subprocess, sys, tempfile, time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
PIN_FILE = WORKSPACE / 'Workflow' / 'hyperframes-pin.txt'   # optional: one line with a version to pin every project to
DEFAULT_VERSION = os.environ.get('HYPERFRAMES_VERSION') or (PIN_FILE.read_text().strip() if PIN_FILE.is_file() else '') or 'latest'
EXTS = {'.html', '.htm', '.css', '.js', '.mjs', '.json'}
# scratch/ holds throwaway probes (e.g. 5 s openings cut from a full timeline) that are wrong on purpose
SKIP_PARTS = {'node_modules', 'renders', '12-Archive', '.git', 'scratch'}
STATE = Path(tempfile.gettempdir()) / 'hf-lint-hook'


def project_root(path):
    p = Path(path).resolve()
    if any(part in SKIP_PARTS or part.startswith('backup-') for part in p.parts):
        return None
    for d in [p] + list(p.parents):
        if d == WORKSPACE.parent:
            break
        if (d / 'hyperframes.json').is_file() or ((d / 'index.html').is_file() and (d / 'compositions').is_dir()):
            return d
    return None


def version_for(root):
    try:
        scripts = json.loads((root / 'package.json').read_text()).get('scripts', {})
        m = re.search(r'hyperframes@([0-9][\w.\-]*)', ' '.join(scripts.values()))
        if m:
            return m.group(1)
    except (OSError, ValueError):
        pass
    return DEFAULT_VERSION


def accepted(root):
    out = set()
    f = root / '.hyperframes-lint-accept'
    if f.is_file():
        for line in f.read_text().splitlines():
            parts = line.split('#', 1)[0].split()
            if len(parts) >= 2:
                out.add((parts[0], parts[1]))
    return out


def lint(root):
    """Return (blocking findings, note) for one project."""
    cmd = ['npx', '--yes', f'hyperframes@{version_for(root)}', 'lint', '--json', str(root)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=root)
    except (subprocess.TimeoutExpired, OSError) as e:
        return [], f'hyperframes lint could not run for {root}: {e}'
    try:
        data = json.loads(r.stdout[r.stdout.index('{'):])
    except ValueError:
        return [], f'hyperframes lint gave no JSON for {root}: {r.stderr.strip()[-300:]}'
    acc = accepted(root)
    block = [f for f in data.get('findings', [])
             if f.get('severity') == 'error'
             or (f.get('severity') == 'warning'
                 and (f.get('code'), f.get('elementId') or '*') not in acc and (f.get('code'), '*') not in acc)]
    return block, ''


def report(results):
    lines = []
    for root, findings in results:
        rel = os.path.relpath(root, WORKSPACE)
        lines.append(f'HyperFrames lint: {len(findings)} finding(s) to fix in {rel}')
        for f in findings:
            where = os.path.relpath(f['file'], root) if f.get('file') else ''
            el = f" [{f['elementId']}]" if f.get('elementId') else ''
            lines.append(f"- {f.get('severity', '?').upper()} {f.get('code')}{el} {where}: {f.get('message', '')}")
            if f.get('fixHint'):
                lines.append(f"  Fix: {f['fixHint']}")
    lines.append('Fix these now, then re-run lint (`npx hyperframes@<pinned> lint` in the project). Errors must be fixed. '
                 'A warning that is truly intentional may be accepted with a line "<code> <elementId>  # reason" in '
                 '<project>/.hyperframes-lint-accept; say so to the user. Never silence a finding by deleting content.')
    return '\n'.join(lines)


def remember(session, root):
    if not session:
        return
    STATE.mkdir(exist_ok=True)
    f = STATE / f'{re.sub(r"[^A-Za-z0-9_-]", "", session)}.txt'
    known = set(f.read_text().split('\n')) if f.exists() else set()
    if str(root) not in known:
        with f.open('a') as h:
            h.write(str(root) + '\n')


def touched(session):
    roots = set()
    f = STATE / f'{re.sub(r"[^A-Za-z0-9_-]", "", session or "")}.txt'
    if session and f.exists():
        roots |= {Path(p) for p in f.read_text().split('\n') if p}
    cutoff = time.time() - 3600                     # catches edits made through Bash/python, not Edit/Write
    for base in [WORKSPACE / 'Videos', WORKSPACE / 'Workflow' / 'Pipelines']:
        for hj in base.rglob('hyperframes.json'):
            root = project_root(hj)
            if not root:
                continue
            for p in [root / 'index.html', *root.glob('compositions/*.html')]:
                if p.is_file() and p.stat().st_mtime > cutoff:
                    roots.add(root)
                    break
    return sorted(r for r in roots if r.is_dir())


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if mode == 'check':
        roots = sorted({r for r in (project_root(a) for a in (sys.argv[2:] or [os.getcwd()])) if r})
        if not roots:
            print('No HyperFrames project found (needs hyperframes.json, or index.html + compositions/).'); return 0
        results = [(r, lint(r)[0]) for r in roots]
        bad = [(r, f) for r, f in results if f]
        print(report(bad) if bad else f'HyperFrames lint clean: {", ".join(os.path.relpath(r, WORKSPACE) for r in roots)}')
        return 1 if bad else 0

    try:
        hook = json.load(sys.stdin)
    except ValueError:
        return 0
    session = hook.get('session_id', '')
    if mode == 'post':
        ti = hook.get('tool_input') or {}
        paths = [ti.get('file_path') or ti.get('notebook_path') or ''] if isinstance(ti, dict) else []
        # Codex edits with apply_patch: the paths are inside the patch text ("*** Update File: x")
        blob = json.dumps(ti) if not isinstance(ti, str) else ti
        paths += re.findall(r'\*\*\* (?:Add|Update) File: ([^\\\n"]+)', blob)
        paths += re.findall(r'\*\*\* Move to: ([^\\\n"]+)', blob)
        cwd = Path(hook.get('cwd') or os.getcwd())
        roots = []
        for p in paths:
            p = p.strip()
            if not p or Path(p).suffix.lower() not in EXTS:
                continue
            r = project_root(p if os.path.isabs(p) else cwd / p)
            if r and r not in roots:
                roots.append(r)
        if not roots:
            return 0
        root = roots[0]
        remember(session, root)
        findings, note = lint(root)
        if note:
            print(note, file=sys.stderr); return 0      # a broken lint run must never block editing
        if findings:
            print(report([(root, findings)]), file=sys.stderr); return 2
        return 0
    if mode == 'stop':
        if hook.get('stop_hook_active'):
            return 0                                   # already continued once for this stop; don't loop
        bad = []
        for root in touched(session):
            findings, _ = lint(root)
            if findings:
                bad.append((root, findings))
        if bad:
            print(report(bad), file=sys.stderr); return 2
        return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
