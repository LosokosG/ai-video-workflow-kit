#!/usr/bin/env python3
"""Check what this machine has for the workflow. Read-only, stdlib only.

  check_setup.py            table of required / recommended / optional tools; exit 1 if a required one is missing
  check_setup.py --json     same as JSON (for an agent)
"""
import importlib.util, json, platform, shutil, subprocess, sys


def version(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (r.stdout or r.stderr).strip().splitlines()[0][:70]
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return ''


def venv_python():
    import os
    from pathlib import Path
    for c in (os.environ.get('WHISPER_PY'), str(Path(__file__).resolve().parents[1] / '.venv' / 'bin' / 'python'),
              str(Path(__file__).resolve().parents[1] / '.venv' / 'Scripts' / 'python.exe')):
        if c and Path(c).is_file():
            return c
    return None


def has_module(name):
    """True if the module imports in this Python or in the workflow venv (Workflow/Tools/.venv or $WHISPER_PY)."""
    if importlib.util.find_spec(name) is not None:
        return True
    py = venv_python()
    return bool(py) and subprocess.run([py, '-c', f'import {name}'], capture_output=True).returncode == 0


def node_major():
    v = version(['node', '--version'])
    try:
        return int(v.lstrip('v').split('.')[0])
    except ValueError:
        return 0


checks = [
    # (tier, name, ok, detail, used by)
    ('required', 'Python 3.10+', sys.version_info >= (3, 10), platform.python_version(), 'all tools'),
    ('required', 'ffmpeg', bool(shutil.which('ffmpeg')), version(['ffmpeg', '-version']), 'study.py, renders, audio'),
    ('required', 'ffprobe', bool(shutil.which('ffprobe')), '', 'study.py, footage probing'),
    ('required', 'Node.js 22+ and npx', node_major() >= 22 and bool(shutil.which('npx')), version(['node', '--version']), 'HyperFrames (motion graphics, renders, lint)'),
    ('required', 'git', bool(shutil.which('git')), version(['git', '--version']), 'skills install, tracking changes'),
    ('recommended', 'yt-dlp', bool(shutil.which('yt-dlp')), version(['yt-dlp', '--version']), 'video-study, video-ideas, video-packaging'),
    ('recommended', 'faster-whisper (Python)', has_module('faster_whisper'), '', 'local transcription in study.py (set WHISPER_PY if it is in another venv)'),
    ('recommended', 'Pillow (Python)', has_module('PIL'), '', 'packaging/feedcheck.py thumbnail checks'),
    ('recommended', '7-Zip (7z / 7zz)', bool(shutil.which('7z') or shutil.which('7zz')), '', 'video-closeout archives'),
    ('recommended', 'a trash tool (gio / trash-put / trash) or send2trash', bool(shutil.which('gio') or shutil.which('trash-put') or shutil.which('trash') or has_module('send2trash')), '', 'moving files to the trash instead of deleting'),
    ('optional', 'HyperFrames skills installed', False, '', 'run `npx skills add heygen-com/hyperframes` in the workspace (see docs/SETUP.md)'),
    ('optional', 'Demucs (Python)', has_module('demucs'), '', 'Tools/stems music stem splitting'),
    ('optional', 'A video editor (DaVinci Resolve, Premiere, Final Cut, Kdenlive…)', None, 'not detectable; ask the user', 'the cut itself, colour, delivery'),
]

from pathlib import Path
root = Path(__file__).resolve().parents[3]
skills = root / '.agents' / 'skills'
checks[10] = ('optional', 'HyperFrames skills installed', (skills / 'hyperframes').is_dir(), str(skills / 'hyperframes'), 'run `npx skills add heygen-com/hyperframes` in the workspace (see docs/SETUP.md)')

if '--json' in sys.argv:
    print(json.dumps([dict(tier=t, name=n, ok=o, detail=d, used_by=u) for t, n, o, d, u in checks], indent=1))
else:
    print(f'{platform.system()} {platform.machine()}, Python {platform.python_version()}\n')
    for t, n, o, d, u in checks:
        mark = '  ?  ' if o is None else ('  ok ' if o else 'MISSING')
        print(f'[{mark}] {t:11} {n:52} {d}\n{"":20}used by: {u}')
sys.exit(1 if any(t == 'required' and not o for t, n, o, d, u in checks) else 0)
