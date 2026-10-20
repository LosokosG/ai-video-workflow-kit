import json
import os
import runpy
import subprocess
import sys

import pytest

from conftest import copy_tool, skip_windows


@pytest.fixture
def ws(tmp_path):
    root = tmp_path / 'ws'
    for name in ('alpha', 'beta'):
        (root / '.agents' / 'skills' / name).mkdir(parents=True)
        (root / '.agents' / 'skills' / name / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: x\n---\n')
    (root / '.agents' / 'skills' / 'not-a-skill').mkdir()
    (root / 'AGENTS.md').write_text('# instructions\n')
    return root


def run(script, *args, env=None, cwd=None):
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, env=env, cwd=cwd,
                          timeout=60)


# ---------------------------------------------------------------- link_skills.py

@skip_windows
def test_link_skills_makes_relative_symlinks_and_is_idempotent(ws):
    script = copy_tool('setup/link_skills.py', ws)
    r = run(script)
    assert r.returncode == 0 and r.stdout.strip() == 'linked 3: alpha, beta, CLAUDE.md'
    links = ws / '.claude' / 'skills'
    assert sorted(p.name for p in links.iterdir()) == ['alpha', 'beta']
    assert os.readlink(links / 'alpha') == os.path.join('..', '..', '.agents', 'skills', 'alpha')
    assert (links / 'alpha' / 'SKILL.md').read_text().startswith('---\nname: alpha')
    assert os.readlink(ws / 'CLAUDE.md') == 'AGENTS.md'

    r = run(script)
    assert r.stdout.strip() == 'nothing to do: every skill is already linked'


@skip_windows
def test_link_skills_never_replaces_existing_entries(ws):
    own = ws / '.claude' / 'skills' / 'beta'
    own.mkdir(parents=True)
    (own / 'mine.txt').write_text('keep me')
    (ws / 'CLAUDE.md').write_text('my own file')
    r = run(copy_tool('setup/link_skills.py', ws))
    assert r.stdout.strip() == 'linked 1: alpha'
    assert (own / 'mine.txt').read_text() == 'keep me' and not own.is_symlink()
    assert (ws / 'CLAUDE.md').read_text() == 'my own file'


def test_link_skills_copies_when_symlinks_fail(ws, monkeypatch, capsys):
    script = copy_tool('setup/link_skills.py', ws)

    def no_symlinks(*a, **k):
        raise OSError('symlinks not allowed')

    monkeypatch.setattr(os, 'symlink', no_symlinks)
    runpy.run_path(str(script), run_name='__main__')
    out = capsys.readouterr().out
    assert 'linked 3' in out and 'files were copied' in out
    copied = ws / '.claude' / 'skills' / 'alpha'
    assert copied.is_dir() and not copied.is_symlink() and (copied / 'SKILL.md').is_file()
    assert (ws / 'CLAUDE.md').read_text() == '# instructions\n' and not (ws / 'CLAUDE.md').is_symlink()


# ---------------------------------------------------------------- check_setup.py --json

TOOL_STUBS = {
    'ffmpeg': 'print("ffmpeg version 7.1 Copyright (c) the FFmpeg developers")',
    'ffprobe': 'print("ffprobe version 7.1")',
    'node': 'print("v22.11.0")',
    'npx': 'print("10.9.0")',
    'git': 'print("git version 2.47.0")',
    '7z': 'print("7-Zip 24.08")',
}


def check(ws, fakebin, *names, node='v22.11.0'):
    for n in names:
        fakebin(n, TOOL_STUBS[n] if n != 'node' else f'print("{node}")')
    script = copy_tool('setup/check_setup.py', ws)
    env = {'PATH': str(fakebin.dir), 'HOME': str(ws.parent), 'PYTHONNOUSERSITE': '1'}
    r = run(script, '--json', env=env)
    return r, (json.loads(r.stdout) if r.stdout.strip() else None)


@skip_windows
def test_check_setup_json_shape_with_everything_required(ws, fakebin):
    r, rows = check(ws, fakebin, 'ffmpeg', 'ffprobe', 'node', 'npx', 'git', '7z')
    assert r.returncode == 0, r.stderr
    assert isinstance(rows, list) and len(rows) == 13
    for row in rows:
        assert set(row) == {'tier', 'name', 'ok', 'detail', 'used_by'}
        assert row['tier'] in {'required', 'recommended', 'optional'}
        assert row['ok'] in (True, False, None) and isinstance(row['detail'], str) and row['used_by']
    by = {row['name']: row for row in rows}
    assert [row['name'] for row in rows if row['tier'] == 'required'] == [
        'Python 3.10+', 'ffmpeg', 'ffprobe', 'Node.js 22+ and npx', 'git']
    assert all(row['ok'] for row in rows if row['tier'] == 'required')
    assert by['ffmpeg']['detail'].startswith('ffmpeg version 7.1')
    assert by['Node.js 22+ and npx']['detail'] == 'v22.11.0'
    assert by['yt-dlp']['ok'] is False                          # not stubbed
    assert by['7-Zip (7z / 7zz)']['ok'] is True
    assert by['HyperFrames skills installed']['ok'] is False
    assert by['A video editor (DaVinci Resolve, Premiere, Final Cut, Kdenlive…)']['ok'] is None


@skip_windows
def test_check_setup_sees_installed_hyperframes_skills(ws, fakebin):
    (ws / '.agents' / 'skills' / 'hyperframes').mkdir()
    _, rows = check(ws, fakebin, 'ffmpeg', 'ffprobe', 'node', 'npx', 'git')
    assert {r['name']: r['ok'] for r in rows}['HyperFrames skills installed'] is True


@skip_windows
def test_check_setup_exits_1_when_required_tools_are_missing(ws, fakebin):
    r, rows = check(ws, fakebin, 'git')
    assert r.returncode == 1
    by = {row['name']: row['ok'] for row in rows}
    assert by['ffmpeg'] is False and by['Node.js 22+ and npx'] is False and by['git'] is True


@skip_windows
def test_check_setup_rejects_old_node(ws, fakebin):
    r, rows = check(ws, fakebin, 'ffmpeg', 'ffprobe', 'node', 'npx', 'git', node='v20.18.0')
    assert r.returncode == 1
    assert {row['name']: row['ok'] for row in rows}['Node.js 22+ and npx'] is False
