#!/usr/bin/env python3
"""Pack a finished video's raw footage into two lossless 7-Zip archives and prove every file survives.

  archive_raw.py VIDEO_DIR USED_LIST

USED_LIST: text file, one entry per line, naming the 01-Raw files the final edit uses (file name or its SHA-256
prefix). Everything else in 01-Raw counts as an outtake. Writes, in VIDEO_DIR/12-Archive/:
  raw-footage-used-in-final.7z, outtakes-unused-takes.7z, raw-archive-manifest.json
Each file's SHA-256 is taken before packing (or read from a 64-hex name prefix if the file name starts with one).
Then each is extracted from the archive and re-hashed. Nothing is deleted; the script prints what can go to the
trash once you (and the user) are satisfied. Refuses to overwrite an existing archive.
"""
import hashlib, json, re, subprocess, sys, time
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def main(video_dir, used_list):
    vd = Path(video_dir).resolve(); raw = vd / '01-Raw'; out = vd / '12-Archive'; out.mkdir(exist_ok=True)
    files = sorted(p for p in raw.iterdir() if p.is_file() and not p.is_symlink())
    wanted = {l.strip() for l in Path(used_list).read_text().splitlines() if l.strip()}
    rows = []
    for p in files:
        m = re.match(r'([0-9a-f]{64})-', p.name)
        digest = m.group(1) if m else sha(p)
        used = p.name in wanted or any(digest.startswith(w) for w in wanted if re.fullmatch(r'[0-9a-f]{8,64}', w))
        rows.append({'name': p.name, 'bytes': p.stat().st_size, 'sha256': digest, 'used_in_final': used})
    groups = {'raw-footage-used-in-final.7z': [r for r in rows if r['used_in_final']],
              'outtakes-unused-takes.7z': [r for r in rows if not r['used_in_final']]}
    for arc, members in groups.items():
        if not members:
            continue
        dst = out / arc
        if dst.exists():
            sys.exit(f'Exists: {dst}')
        lst = out / (arc + '.list')
        lst.write_text(''.join(r['name'] + '\n' for r in members))
        subprocess.run(['7z', 'a', '-t7z', '-mx=1', '-mmt=on', str(dst), f'@{lst}'], cwd=raw, check=True,
                       stdout=subprocess.DEVNULL)
        lst.unlink()
        subprocess.run(['7z', 't', str(dst)], check=True, stdout=subprocess.DEVNULL)
        for r in members:
            p = subprocess.Popen(['7z', 'e', '-so', str(dst), r['name']], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            h = hashlib.sha256()
            for b in iter(lambda: p.stdout.read(1 << 22), b''):
                h.update(b)
            p.wait()
            r['archive'] = arc
            r['verified_from_archive'] = h.hexdigest() == r['sha256']
    manifest = {'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'video': vd.name, 'files': rows,
                'all_verified': all(r.get('verified_from_archive') for r in rows),
                'restore': 'cd 01-Raw && 7z x ../12-Archive/<archive>.7z'}
    (out / 'raw-archive-manifest.json').write_text(json.dumps(manifest, indent=1))
    ok = manifest['all_verified']
    print(f"{len(rows)} files, {sum(r['used_in_final'] for r in rows)} used / {sum(not r['used_in_final'] for r in rows)} outtakes, "
          f"all verified: {ok}")
    if ok:
        print('Safe to move the loose 01-Raw files to the trash after the user approves (OS trash, e.g. `gio trash` on Linux; never delete).')
    else:
        sys.exit('Verification failed: keep the loose files.')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
