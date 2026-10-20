import hashlib
import json
import os
import subprocess
import sys

import pytest

from conftest import TOOLS, skip_windows

pytestmark = skip_windows

# A stand-in for the 7z CLI with the three verbs archive_raw.py uses, backed by a zip file.
FAKE_7Z = r'''import os, sys, zipfile
verb, args = sys.argv[1], sys.argv[2:]
if verb == 'a':
    dst = [a for a in args if not a.startswith('-') and not a.startswith('@')][0]
    names = open([a for a in args if a.startswith('@')][0][1:]).read().split('\n')
    with zipfile.ZipFile(dst, 'w') as z:
        for n in filter(None, names):
            z.write(n, n)
elif verb == 't':
    with zipfile.ZipFile(args[0]) as z:
        sys.exit(1 if z.testzip() else 0)
elif verb == 'e':
    arc, name = [a for a in args if a != '-so']
    with zipfile.ZipFile(arc) as z:
        data = z.read(name)
    sys.stdout.buffer.write(b'corrupted' if os.environ.get('FAKE7Z_CORRUPT') else data)
'''


@pytest.fixture
def video(tmp_path, fakebin):
    fakebin('7z', FAKE_7Z)
    vd = tmp_path / 'Videos' / '2026-01-01-demo'
    raw = vd / '01-Raw'
    raw.mkdir(parents=True)
    files = {'take-01.mov': b'first take', 'take-02.mov': b'second take' * 1000, 'screen.mkv': b'screen'}
    for name, data in files.items():
        (raw / name).write_bytes(data)
    digest = hashlib.sha256(b'pre-hashed').hexdigest()
    (raw / f'{digest}-phone.mp4').write_bytes(b'pre-hashed')          # name carries its own SHA-256
    files[f'{digest}-phone.mp4'] = b'pre-hashed'
    (raw / 'link.mov').symlink_to(raw / 'take-01.mov')                  # symlinks are not archived
    used = tmp_path / 'used.txt'
    used.write_text(f'take-01.mov\n\n{digest[:12]}\n')                  # by file name and by hash prefix
    return vd, used, files, fakebin.dir


def run(vd, used, bindir, **env):
    e = dict(os.environ, PATH=f'{bindir}{os.pathsep}{os.environ.get("PATH", "")}', **env)
    return subprocess.run([sys.executable, str(TOOLS / 'closeout' / 'archive_raw.py'), str(vd), str(used)],
                          capture_output=True, text=True, env=e, timeout=60)


def test_manifest_records_hashes_groups_and_verification(video):
    vd, used, files, bindir = video
    r = run(vd, used, bindir)
    assert r.returncode == 0, r.stderr
    assert '4 files, 2 used / 2 outtakes, all verified: True' in r.stdout
    m = json.loads((vd / '12-Archive' / 'raw-archive-manifest.json').read_text())
    assert m['video'] == '2026-01-01-demo' and m['all_verified'] is True
    rows = {row['name']: row for row in m['files']}
    assert set(rows) == set(files)
    for name, data in files.items():
        assert rows[name]['sha256'] == hashlib.sha256(data).hexdigest()
        assert rows[name]['bytes'] == len(data)
        assert rows[name]['verified_from_archive'] is True
    used_names = {n for n, row in rows.items() if row['used_in_final']}
    assert used_names == {'take-01.mov', next(n for n in files if n.endswith('-phone.mp4'))}
    assert {rows[n]['archive'] for n in used_names} == {'raw-footage-used-in-final.7z'}
    assert rows['screen.mkv']['archive'] == 'outtakes-unused-takes.7z'
    assert sorted(p.name for p in (vd / '12-Archive').iterdir()) == [
        'outtakes-unused-takes.7z', 'raw-archive-manifest.json', 'raw-footage-used-in-final.7z']
    assert sorted(p.name for p in (vd / '01-Raw').iterdir()) == sorted(list(files) + ['link.mov'])  # nothing deleted


def test_refuses_to_overwrite_an_existing_archive(video):
    vd, used, _, bindir = video
    assert run(vd, used, bindir).returncode == 0
    r = run(vd, used, bindir)
    assert r.returncode != 0 and 'Exists:' in r.stderr


def test_failed_verification_keeps_the_loose_files(video):
    vd, used, _, bindir = video
    r = run(vd, used, bindir, FAKE7Z_CORRUPT='1')
    assert r.returncode != 0 and 'Verification failed' in r.stderr
    m = json.loads((vd / '12-Archive' / 'raw-archive-manifest.json').read_text())
    assert m['all_verified'] is False
