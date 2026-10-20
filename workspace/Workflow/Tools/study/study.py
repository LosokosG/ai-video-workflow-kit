#!/usr/bin/env python3
"""Helpers for studying a video (YouTube link or local file). Stdlib only; needs ffmpeg/ffprobe and yt-dlp.

  study.py fetch URL STUDYDIR                 description, chapters, transcript, the largest thumbnail (original JPEG),
                                              most-replayed heatmap and download-size estimates; no video. Says so when
                                              there are no chapters or no heatmap. Raw yt-dlp files go to STUDYDIR/scratch/
  study.py segment URL START END OUT [--audio] [--height N]
                                              download START..END (seconds or mm:ss); --audio = audio only. Prints a size and
                                              time estimate first. START 0 with END >= the video's length is a normal (fast)
                                              download; a section streams through ffmpeg (video at up to real time) and a webm
                                              audio section snaps back to a cue point. The result is checked with ffprobe (it
                                              decodes; video and audio cover the range within 1 s): on failure it exits
                                              non-zero, renames the file *.broken and writes no sidecar. Partial files from the
                                              run go to the trash. OUT.json records the measured source start (source_start_s),
                                              which every command uses to map clip times back to source time.
  study.py frames VIDEO T1,T2,... OUTDIR      one JPEG per time (times within VIDEO; files are named by source time)
  study.py sheet VIDEO OUT.jpg [EVERY] [--start T] [--end T]
                                              contact sheets, one thumb every EVERY s (default 10), the first frame at or after
                                              each slot, each stamped with its source time; 36 per sheet (row by row); more than
                                              36 thumbnails go to OUT-01.jpg, OUT-02.jpg… Prints the name of every file written.
                                              --start/--end limit the range (times within VIDEO, like `frames`)
  study.py analyze VIDEO OUT.json [--fine] [--start T] [--end T] [--crop W:H:X:Y]
                                              hard cuts and visual changes (bursts < 0.2 s apart merged), new-element onsets
                                              (estimate), still stretches, loudness over time (says so when there's no audio);
                                              --start/--end measure only that range (times within VIDEO; output in source time);
                                              --crop measures the picture only in that pixel rectangle (width:height:left:top,
                                              e.g. the content window beside a presenter inset); audio stays the whole mix
  study.py pauses MEDIA OUT.json [--ranges A-B,C-D]
                                              words per minute, pauses, speech vs pause loudness (local whisper); --ranges =
                                              only these narration ranges (times within MEDIA). Retries a range that returns
                                              < 30 words/min over speech-level sound, and warns if it stays low. duration_s is
                                              the measured length (the ranges' total); file_duration_s is the whole file
  study.py transcribe MEDIA OUT.txt [--start T] [--end T] [--words]
                                              local speech-to-text with timestamps (source time) and the first word's time;
                                              --words also writes OUT.words.json: every word with its start and end (source time)
  study.py examples SPEC.json VIDEO TRANSCRIPT OUTROOT
                                              tactic example folders OUTROOT/<slug>/examples/: transcript excerpt (source URL
                                              with &t= on line 1), native-size frames <mmss>-<what>.jpg, <= 20 s H.264/AAC clips;
                                              identical files are hardlinked; a second source's files get its prefix; writes
                                              SPEC.manifest.json. SPEC = {"source": {"url", "title", "prefix", "captions"},
                                              "tactics": {slug: {"transcript": [[a, b]], "frames": [[t, what]],
                                              "clips": [[a, b, what]], "copy": [[path, name]]}}}; times are source times.
                                              url/title/captions default to TRANSCRIPT's meta.json (from `fetch`).

Times printed for a clip made by `segment` are converted to source time when its OUT.json sidecar is present.
"""
import hashlib, html, json, math, os, re, shutil, subprocess, sys, statistics, tempfile, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WHISPER_PY = os.environ.get('WHISPER_PY', sys.executable)    # interpreter that has faster-whisper installed
WHISPER = os.environ.get('WHISPER_MODEL', 'small')         # model name (downloaded on first use) or a local model directory
TIMING = re.compile(r'^((?:\d+:)?\d+:\d+[.,]\d+)\s+-->\s+((?:\d+:)?\d+:\d+[.,]\d+)')


def secs(t):
    t = str(t).strip().replace(',', '.')
    if ':' in t:
        parts = [float(p) for p in t.split(':')]
        return sum(p * 60 ** i for i, p in enumerate(reversed(parts)))
    return float(t)


def stamp(s, tenths=False):
    if tenths:
        return f'{int(s // 60):02d}:{s % 60:04.1f}'
    s = int(s)
    return f'{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}' if s >= 3600 else f'{s // 60:02d}:{s % 60:02d}'


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def trash(paths):
    """Move files to the OS trash (never delete): gio (Linux), trash-put / trash (Linux, macOS), else the send2trash module."""
    paths = [str(p) for p in paths]
    for cmd in (['gio', 'trash'], ['trash-put'], ['trash']):
        if shutil.which(cmd[0]):
            if run(cmd + paths).returncode == 0:
                return
    try:
        from send2trash import send2trash
        for p in paths:
            send2trash(p)
    except ImportError:
        print('No trash tool found (gio, trash-put, trash, send2trash); left in place: ' + ', '.join(paths))


def parse(args, valued=()):
    """Split CLI args into positionals and {--flag: value or True}."""
    pos, kw, it = [], {}, iter(args)
    for a in it:
        if a in valued:
            kw[a] = next(it, None)
        elif a.startswith('--'):
            kw[a] = True
        else:
            pos.append(a)
    return pos, kw


def sidecar(media):
    side = Path(str(media) + '.json')
    return json.loads(side.read_text()) if side.exists() else {}


def offset_of(media):
    return float(sidecar(media).get('source_start_s', 0))


def duration(media):
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(media)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def span_args(media, kw, dur=None):
    """--start/--end (times within MEDIA) -> (start, end, ffmpeg input args). Input seeking, so only that range is decoded."""
    dur = duration(media) if dur is None else dur
    s0 = secs(kw.get('--start') or 0); s1 = min(secs(kw['--end']), dur) if kw.get('--end') else dur
    if s1 <= s0:
        sys.exit(f'empty range {s0:g}–{s1:g} s (the file is {dur:g} s)')
    return s0, s1, [*(['-ss', f'{s0:.3f}'] if s0 else []), *(['-to', f'{s1:.3f}'] if s1 < dur else []), '-i', str(media)]


def wav16k(inp, dst):
    run(['ffmpeg', '-v', 'error', '-y', *inp, '-vn', '-ac', '1', '-ar', '16000', str(dst)])
    return str(dst)


def vtt_to_lines(path):
    """Parse cue by cue (split on timing lines, not blank lines: YouTube cues contain whitespace-only lines).
    Auto-captions repeat each line while it scrolls; keep each new line once, stamped with the cue where it appears."""
    cues, cur = [], None
    for raw in Path(path).read_text(errors='replace').splitlines():
        m = TIMING.match(raw.strip())
        if m:
            cur = [secs(m.group(1)), secs(m.group(2)), []]
            cues.append(cur)
        elif cur is not None and raw.strip():
            cur[2].append(html.unescape(re.sub(r'<[^>]+>', '', raw)).strip())
    out = []
    for start, end, lines in cues:
        if end - start < 0.05:            # 10 ms "hold" cues only repeat text already shown
            continue
        for line in lines:
            if line and all(line != prev for _, prev in out[-3:]):
                out.append((start, line))
    return out


def caption_choices(info):
    """Manual subtitles first (English, then the original language); else the original-language ASR (`xx-orig`);
    else plain `en`, which on dubbed videos may be a machine translation. Only tracks the video has, best first."""
    lang = (info.get('language') or 'en').split('-')[0]
    manual = set((info.get('subtitles') or {}).keys()) - {'live_chat'}
    auto = set((info.get('automatic_captions') or {}).keys())
    asr = 'auto (original-language speech recognition)'
    choices = [(l, 'manual') for l in ('en', 'en-US', 'en-GB', lang) if l in manual]
    choices += [(l, asr) for l in (f'{lang}-orig', 'en-orig') if l in auto]
    choices += [(l, k) for l, k in ((lang, 'auto'), ('en', 'auto' if lang == 'en' else 'auto-TRANSLATED into English — check against the audio')) if l in auto]
    return list(dict.fromkeys(choices))


VIDEO_FMT = 'bv*[height<={h}]+ba[format_note*=original]/bv*[height<={h}]+ba/b[height<={h}]'
AUDIO_FMT = 'ba[format_note*=original]/ba'


def size_estimates(info_json, duration_s, fmts=None):
    """Ask yt-dlp (offline, from the saved info file) which formats `segment` would download, and their bitrate."""
    est = {}
    fmts = fmts or (('video_1080p_with_audio', VIDEO_FMT.format(h=1080)), ('video_720p_with_audio', VIDEO_FMT.format(h=720)),
                    ('audio_only', AUDIO_FMT))
    for key, fmt in fmts:
        r = run(['yt-dlp', '--load-info-json', str(info_json), '-f', fmt, '--skip-download', '--print',
                 '%(format_id)s|%(tbr)s|%(vcodec)s|%(acodec)s'])
        try:
            fid, tbr, vc, ac = r.stdout.strip().splitlines()[-1].split('|')
            mb_min = float(tbr) * 60 / 8 / 1000
            est[key] = {'format': fid, 'MB_per_min': round(mb_min, 2), 'whole_video_MB': round(mb_min * (duration_s or 0) / 60, 1),
                        'video': vc not in ('none', 'NA'), 'audio': ac not in ('none', 'NA') or '+' in fid}
        except (ValueError, IndexError):
            est[key] = None
    return est


def save_thumbnail(info, dst):
    """The original bytes of the largest thumbnail YouTube has (maxresdefault.jpg when it exists), not yt-dlp's
    webp-to-jpg re-encode. Falls back down YouTube's list; converts only when no JPEG can be had."""
    thumbs = sorted(info.get('thumbnails') or [], key=lambda t: t.get('preference') or -99, reverse=True)
    urls = [u for u in dict.fromkeys([t['url'] for t in thumbs] + [info.get('thumbnail')]) if u]
    for u in sorted(urls, key=lambda u: not u.split('?')[0].endswith('.jpg')):   # stable: largest JPEG first; 404s are skipped
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as r:
                data = r.read()
        except OSError:
            continue
        wh = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', '-i', 'pipe:0'],
                            input=data, capture_output=True).stdout.decode().strip()
        w, h = (int(x) for x in wh.split(',')[:2]) if re.match(r'\d+,\d+', wh) else (0, 0)
        if w <= 120:                      # YouTube's grey placeholder
            continue
        if u.split('?')[0].endswith('.jpg'):
            dst.write_bytes(data); note = 'original JPEG'
        else:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'pipe:0', '-q:v', '2', str(dst)], input=data, capture_output=True)
            note = 'converted from ' + u.split('?')[0].rsplit('.', 1)[-1]
        return {'url': u, 'width': w, 'height': h, 'bytes': dst.stat().st_size, 'note': note}
    return None


def cmd_fetch(url, studydir):
    out = Path(studydir); scratch = out / 'scratch'; scratch.mkdir(parents=True, exist_ok=True)
    r = run(['yt-dlp', '--skip-download', '--write-info-json', '--no-playlist', '-o', str(scratch / 'source.%(ext)s'), url])
    info_json = scratch / 'source.info.json'
    if not info_json.exists():
        sys.exit(r.stderr[-2000:])
    info = json.loads(info_json.read_text())
    (out / 'description.txt').write_text(info.get('description') or '')
    notes = []
    chapters = info.get('chapters') or []
    if chapters:
        (out / 'chapters.txt').write_text(''.join(f"{stamp(c['start_time'])} {c.get('title', '')}\n" for c in chapters))
    else:
        notes.append('No chapters in the metadata: chapters.txt not written.')
    thumb = save_thumbnail(info, out / 'thumbnail.jpg')
    if not thumb:
        notes.append('No thumbnail could be downloaded.')
    vtt = lang = kind = None
    for l, k in caption_choices(info):   # one track only: `en` and `en-orig` are often byte-identical
        f = scratch / f'source.{l}.vtt'
        if not f.exists():
            rr = run(['yt-dlp', '--load-info-json', str(info_json), '--skip-download', '--sleep-subtitles', '1',
                      '--write-subs' if k == 'manual' else '--write-auto-subs', '--sub-langs', re.escape(l), '--sub-format', 'vtt',
                      '-o', str(scratch / 'source.%(ext)s')])
            if not f.exists():
                print(f'caption track {l} failed (YouTube sometimes rate-limits; retry later): {rr.stderr.strip()[-300:]}', file=sys.stderr)
                continue
        vtt, lang, kind = f, l, k
        break
    lines = vtt_to_lines(vtt) if vtt else []
    (out / 'transcript.txt').write_text(''.join(f'[{stamp(t)}] {l}\n' for t, l in lines))
    heat = [{'start': round(h['start_time'], 1), 'end': round(h['end_time'], 1), 'value': round(h['value'], 2)}
            for h in info.get('heatmap') or []]
    if not heat:
        notes.append('No most-replayed heatmap for this video (YouTube shows one only when enough viewers replay parts).')
    peaks = sorted(heat, key=lambda h: -h['value'])[:6]
    meta = {k: info.get(k) for k in ('id', 'title', 'channel', 'channel_follower_count', 'upload_date', 'duration',
                                     'view_count', 'like_count', 'comment_count', 'webpage_url', 'language', 'width',
                                     'height', 'fps', 'tags')}
    meta.update(captions={'track': lang, 'type': kind, 'lines': len(lines)}, chapters=len(chapters), thumbnail=thumb,
                most_replayed_peaks=[f"{stamp(h['start'])}–{stamp(h['end'])} ({h['value']})" for h in peaks] or 'none (no heatmap)',
                heatmap=heat, download_estimate=size_estimates(info_json, info.get('duration')), notes=notes)
    (out / 'meta.json').write_text(json.dumps(meta, indent=1))
    summary = {k: meta[k] for k in ('title', 'channel', 'duration', 'language', 'captions', 'chapters', 'thumbnail',
                                     'most_replayed_peaks', 'download_estimate')}
    print(json.dumps(summary, indent=1))
    for n in notes:
        print(n)
    if not lines:
        print('No captions: download the audio (segment --audio 0 END) and run `transcribe`.', file=sys.stderr)
    elif 'TRANSLATED' in (kind or ''):
        print('WARNING: captions are a machine translation; spot-check with `transcribe` on a short clip.', file=sys.stderr)


def stream_spans(path):
    """{'video'|'audio': [first pts, last pts + duration]} from the packets: demux only, quick, catches truncation.
    MP4 section cuts keep the keyframe pre-roll at negative times (hidden by an edit list)."""
    pr = run(['ffprobe', '-v', 'error', '-show_entries', 'stream=index,codec_type', '-of', 'json', str(path)])
    if pr.returncode:
        return None, pr.stderr.strip()[-300:] or 'ffprobe cannot read it'
    types = {s['index']: s['codec_type'] for s in json.loads(pr.stdout).get('streams', [])}
    pk = run(['ffprobe', '-v', 'error', '-show_entries', 'packet=stream_index,pts_time,duration_time', '-of', 'csv=p=0', str(path)])
    spans = {}
    for line in pk.stdout.splitlines():
        f = line.split(',')
        try:
            i, p = int(f[0]), float(f[1])
            d = float(f[2]) if len(f) > 2 and f[2] not in ('', 'N/A') else 0.0
        except (ValueError, IndexError):
            continue
        if types.get(i) in ('video', 'audio'):
            s = spans.setdefault(types[i], [p, p + d]); s[0] = min(s[0], p); s[1] = max(s[1], p + d)
    return spans, pk.stderr.strip()[-300:]


def decode_errors(path):
    """Decode the first and last 3 s of every stream; ffmpeg must stay silent at -v error."""
    errs = []
    for pre, post in (([], ['-t', '3']), (['-sseof', '-3'], [])):
        r = run(['ffmpeg', '-v', 'error', '-nostdin', *pre, '-i', str(path), *post, '-map', '0:v?', '-map', '0:a?', '-f', 'null', '-'])
        if r.returncode or r.stderr.strip():
            errs.append((r.stderr.strip() or f'ffmpeg exit {r.returncode}')[-300:])
    return errs


def partials(folder, stem):
    return {p for p in folder.glob('*') if p.name.startswith(stem + '.') and re.search(r'\.part(-Frag\d+)?$|\.ytdl$|\.temp\.\w+$|\.f\d[\w-]*\.\w+$', p.name)}


def cmd_segment(url, start, end, out, *opts):
    a, b = secs(start), secs(end)
    _, kw = parse(opts, ('--height',))
    audio = '--audio' in kw
    fmt = AUDIO_FMT if audio else VIDEO_FMT.format(h=int(kw.get('--height') or 1080))
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        sys.exit(f'{out} already exists; choose another name (or move the old file to the trash first).')
    old_parts = partials(out.parent, out.stem)
    if old_parts:
        print('Found partial downloads from an earlier run (left alone): ' + ', '.join(p.name for p in sorted(old_parts)))
    with tempfile.TemporaryDirectory() as tmp:
        info_json = Path(tmp) / 'info.json'
        r = run(['yt-dlp', '-J', '--no-playlist', url])
        if r.returncode:
            sys.exit(r.stderr[-2000:])
        info_json.write_text(r.stdout)
        dur = float(json.loads(r.stdout).get('duration') or 0)
        whole = a <= 0 and dur > 0 and b >= dur
        b = min(b, dur) if dur else b
        if b <= a:
            sys.exit(f'nothing to download: START {stamp(a)} is not before END {stamp(b)} (the video is {dur:g} s).')
        est = size_estimates(info_json, dur, [('x', fmt)])['x'] or {}
        span = b - a
        mb = est.get('MB_per_min', 0) * span / 60
        print(f"{'whole file, normal download (network speed)' if whole else 'section via ffmpeg'}: format {est.get('format', '?')}, "
              f"~{mb:.1f} MB" + ('' if whole else f" + up to ~10 s of keyframe pre-roll; video sections stream at up to real time, so up to "
                                 f"~{span / 60:.1f} min (audio is quicker)"), flush=True)
        cmd = ['yt-dlp', '--load-info-json', str(info_json), '-f', fmt, '-o', str(out)]
        if not whole:
            cmd[1:1] = ['--download-sections', f'*{a}-{b}']
        if not audio:
            cmd[1:1] = ['--merge-output-format', 'mp4']
        try:
            r = run(cmd)
            problems = [f'yt-dlp exit {r.returncode}: {r.stderr.strip()[-600:]}'] if r.returncode else []
        except KeyboardInterrupt:
            problems = ['interrupted']
    new_parts = partials(out.parent, out.stem) - old_parts
    if new_parts:
        trash(sorted(new_parts))
        print('Moved leftover partial files from this run to the trash: ' + ', '.join(p.name for p in sorted(new_parts)))
    spans, clip = {}, 0.0
    if not problems and not out.exists():
        problems.append('yt-dlp wrote no file')
    elif not problems:
        spans, err = stream_spans(out)
        if spans is None:
            problems.append(f'unreadable: {err}')
        else:
            need = ['audio'] if audio else [k for k in ('video', 'audio') if est.get(k, True)]
            problems += [f'no {k} stream' for k in need if k not in spans]
            problems += decode_errors(out)
            clip = max((s[1] for s in spans.values()), default=0.0)
            ref = spans.get('audio', spans.get('video', [0, 0]))[1]   # audio packets end exactly at END; video can overrun a frame
            problems += [f'{k} starts {s[0]:.1f} s into the file' for k, s in spans.items() if s[0] > 1.0]
            problems += [f'{k} ends at {s[1]:.1f} s but the file runs to {clip:.1f} s' for k, s in spans.items() if clip - s[1] > 1.0]
    real, how = a, None
    if not problems:
        # Sections end at END but start at the keyframe (MP4: exact, via an edit list) or cue point (webm/mka: up to
        # ~10 s earlier) before START. So the real start is END minus the clip's length; it can never be later than START.
        real = 0.0 if a <= 0 else b - ref
        if whole and abs(clip - dur) > 1.0:
            problems.append(f'the file is {clip:.1f} s long but the video is {dur:g} s')
        elif not whole and real > a + 1.0:
            problems.append(f'the file is {clip:.1f} s long but {b - a:.1f} s was requested: it is cut short')
        elif a > 0 and spans.get('video', [0])[0] < -0.05:
            real, how = a, 'exact: the MP4 keeps the keyframe pre-roll at negative times behind an edit list'
    if problems:
        if out.exists():
            os.replace(out, str(out) + '.broken')
        sys.exit(f'SEGMENT FAILED for {out} (no sidecar written' + (f'; the file is kept as {out.name}.broken' if Path(str(out) + '.broken').exists() else '')
                 + '):\n  - ' + '\n  - '.join(problems))
    size = out.stat().st_size
    meta = {'url': url, 'source_start_s': round(real, 3), 'source_end_s': round(b, 3), 'requested_start_s': a,
            'start_measured_as': 'whole download' if whole else 'no seek (START 0)' if a <= 0 else how or
            'END minus the clip length (a webm/mka section snaps back to a cue point; ~0.02 s)' + ('; END is the video end, rounded to 1 s by YouTube' if b >= dur else ''),
            'format': est.get('format', fmt), 'bytes': size, 'streams_s': {k: [round(x, 3) for x in s] for k, s in spans.items()}}
    Path(str(out) + '.json').write_text(json.dumps(meta, indent=1))
    snap = f' (requested {stamp(a, True)}: snapped back {a - real:.2f} s to a keyframe)' if a - real > 0.05 else ''
    print(out, f'{size / 1e6:.1f} MB', f'source {stamp(real, True)}–{stamp(b, True)}{snap}; verified: decodes, '
          + ', '.join(f'{k} {s[1] - max(s[0], 0):.1f} s' for k, s in sorted(spans.items())))


def cmd_frames(video, times, outdir):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True); off = offset_of(video)
    for t in times.split(','):
        s = secs(t)
        src = s + off
        dst = out / f'{int(src // 60):02d}m{src % 60:04.1f}s.jpg'
        r = run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s:.3f}', '-i', str(video), '-frames:v', '1',
                 '-vf', 'scale=1280:-2', '-q:v', '3', str(dst)])
        if r.returncode or not dst.exists():
            sys.exit(f'frame at {t} failed: {r.stderr.strip()[-300:]}')
        print(dst)


def cmd_sheet(video, out, *args):
    pos, kw = parse(args, ('--start', '--end'))
    every = float(pos[0]) if pos else 10.0
    dur, off = duration(video), offset_of(video)
    s0 = secs(kw.get('--start') or 0); s1 = min(secs(kw['--end']), dur) if kw.get('--end') else dur
    if s1 <= s0:
        sys.exit(f'empty range {s0:g}–{s1:g} s (the file is {dur:g} s)')
    multi = math.ceil((s1 - s0) / every) > 35
    out = Path(out); target = out.with_name(out.stem + '-%02d' + out.suffix) if multi else out
    x = f'trunc((t+{s0 + off:.3f})*10+0.5)'          # source time in tenths of a second
    label = f'%{{eif\\:trunc({x}/600)\\:d\\:2}}\\:%{{eif\\:trunc(mod({x}\\,600)/10)\\:d\\:2}}.%{{eif\\:mod({x}\\,10)\\:d}}'
    vf = (f"select='gte(t,{every}*selected_n-0.001)',showinfo,scale=320:-2,"
          f"drawtext=text='{label}':x=4:y=4:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=3,tile=6x6")
    r = run(['ffmpeg', '-v', 'info', '-nostats', '-nostdin', '-y', *(['-ss', f'{s0:.3f}'] if s0 else []), '-t', f'{s1 - s0:.3f}', '-i', str(video),
             '-an', '-vf', vf, '-fps_mode', 'passthrough', '-q:v', '4', *([] if multi else ['-frames:v', '1']), str(target)])
    times = [float(t) + s0 + off for t in re.findall(r'\] n:\s*\d+ pts:\s*-?\d+ pts_time:(-?[\d.]+)', r.stderr)]
    sheets = math.ceil(len(times) / 36)
    made = [out.with_name(out.stem + f'-{i + 1:02d}' + out.suffix) for i in range(sheets)] if multi else [out]
    if r.returncode or not times or not all(m.exists() for m in made):
        sys.exit(f'sheet failed: {r.stderr.strip()[-600:]}')
    if len(made) == 1 and made[0] != out:          # the up-front estimate expected a second sheet; keep the name asked for
        os.replace(made[0], out); made = [out]
    for i, m in enumerate(made):
        chunk = times[i * 36:(i + 1) * 36]
        print('wrote', m, f'{stamp(chunk[0], True)}–{stamp(chunk[-1], True)}')
    print(f'{len(times)} thumbnails, one every {every:g} s from {stamp(times[0], True)} to {stamp(times[-1], True)} (source time, '
          'stamped top-left), 36 per sheet, row by row' + (f'; {out.name} itself was not written: the sheets are '
          + ', '.join(m.name for m in made) if len(made) > 1 else ''))


def merge_close(times, gap=0.2):
    """One entry per burst: a glitch or flash produces several detections a frame or two apart."""
    out, last = [], None
    for t in times:
        if last is None or t - last > gap:
            out.append(t)
        last = t
    return out


def scene_scores(inp, crop=''):
    """(time, scene score) for every frame whose full-frame (or cropped) change exceeds 0.15, in one decode."""
    r = run(['ffmpeg', '-v', 'info', '-nostats', '-nostdin', *inp, '-an',
             '-vf', f"{crop}scale=320:-2,select='gt(scene,0.15)',metadata=print:key=lavfi.scene_score", '-f', 'null', '-'])
    return [(float(t), float(s)) for t, s in re.findall(r'pts_time:([\d.]+)\s*\n.*?lavfi\.scene_score=([\d.]+)', r.stderr)]


def grey_frames(inp, fps=4, w=64, h=36, crop=''):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', *inp, '-an', '-vf', f'{crop}fps={fps},scale={w}:{h},format=gray',
                        '-f', 'rawvideo', '-'], capture_output=True)
    n = w * h
    return [r.stdout[i:i + n] for i in range(0, len(r.stdout) - n + 1, n)]


def block_diffs(f0, f1, w=64, bw=8, bh=6):
    """Mean absolute difference (0–255) per 8x6-pixel block, row by row, of two tiny grey frames."""
    out = []
    for by in range(0, len(f0) // w, bh):
        for bx in range(0, w, bw):
            s = 0
            for y in range(by, by + bh):
                r = y * w + bx
                s += sum(abs(a - b) for a, b in zip(f0[r:r + bw], f1[r:r + bw]))
            out.append(s / (bw * bh))
    return out


def motion_series(frames):
    """Per-block change between consecutive frames, and its frame mean (the blocks tile the frame): the mean catches
    eased moves that scene detection misses."""
    act = [block_diffs(f0, f1) for f0, f1 in zip(frames, frames[1:])]
    return act, [sum(a) / len(a) for a in act]


def still_stretches(diffs, step, threshold=0.6, min_s=3.0):
    runs, start = [], None
    for i, d in enumerate(diffs + [99]):
        if d < threshold and start is None:
            start = i
        elif d >= threshold and start is not None:
            if (i - start) * step >= min_s:
                runs.append(((i - start) * step, start * step))
            start = None
    return runs


def new_elements(frames, act, step, cuts, k=2, T=4, R=3, Emin=3, gap=0.75):
    """Estimated onsets of new visual elements (titles, cards, layout moves, cuts). A block counts at frame i when its
    content k frames later differs from k frames earlier by > T/255 and by > R x its own change just before and just
    after, i.e. something appeared and stayed while the block was otherwise calm. Gestures and continuous camera
    motion never settle, so they don't count. An onset is a peak of >= Emin such blocks; hard cuts always count; onsets
    closer than `gap` s are one. Tuned on two hand-counted intros (a 19.5 s published
    hook: 9 vs ~11 by eye; a finished video's first 30 s: 16 vs 13-16), with round numbers rather than a per-clip fit."""
    n, E = len(frames), []
    for i in range(n):
        if i < k or i + k + 2 > n - 1:
            E.append(0)
            continue
        P = block_diffs(frames[i - k], frames[i + k])
        before = act[max(0, i - k - 2):i - k]
        pre = [max(c) for c in zip(*before)] if before else [0.0] * len(P)
        post = [max(c) for c in zip(*act[i + k:i + k + 2])]
        E.append(sum(1 for p, a, b in zip(P, pre, post) if p > T and p > R * max(a, b)))
    peaks = [i * step for i in range(n) if E[i] >= Emin and E[i] >= max(E[max(0, i - 2):i + 3]) and not (i and E[i - 1] == E[i])]
    out = []
    for t in sorted(peaks + list(cuts)):
        if not out or t - out[-1] > gap:
            out.append(t)
    return out


def cmd_analyze(video, out, *opts):
    _, kw = parse(opts, ('--start', '--end', '--crop'))
    pr = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]).stdout)
    v = next((s for s in pr['streams'] if s['codec_type'] == 'video'), {})
    has_audio = any(s['codec_type'] == 'audio' for s in pr['streams'])
    s0, s1, inp = span_args(video, kw, float(pr['format'].get('duration', 0)))
    dur = s1 - s0; off = offset_of(video) + s0            # every time below is relative to s0; +off gives source time
    rep = {'file': str(video), 'source_offset_s': offset_of(video), 'range': f'{stamp(off, True)}–{stamp(off + dur, True)}',
           'duration_s': round(dur, 2),
           'video': {k: v.get(k) for k in ('codec_name', 'width', 'height', 'avg_frame_rate', 'pix_fmt', 'color_transfer')}}
    crop = ''
    if kw.get('--crop'):
        try:
            cw, ch, cx, cy = (int(x) for x in kw['--crop'].split(':'))
        except (ValueError, AttributeError):
            sys.exit(f"--crop wants W:H:X:Y in whole pixels (width:height:left:top), got {kw['--crop']!r}")
        fw, fh = v.get('width') or 0, v.get('height') or 0
        if cw < 16 or ch < 16 or cx < 0 or cy < 0 or cx + cw > fw or cy + ch > fh:
            sys.exit(f"--crop {kw['--crop']} is not a rectangle of at least 16x16 inside the {fw}x{fh} frame")
        crop = f'crop={cw}:{ch}:{cx}:{cy},'
        rep['crop'] = {'w': cw, 'h': ch, 'x': cx, 'y': cy, 'of_frame': f'{fw}x{fh}', 'share_of_frame': round(cw * ch / (fw * fh), 3)}
    per_min = lambda n: round(n / (dur / 60), 1) if dur else None
    if v:
        scores = scene_scores(inp, crop)
        hard = merge_close([t for t, s in scores if s > 0.30]); changes = merge_close([t for t, s in scores])
        edges = [0.0] + hard + [dur]; shots = [b - a for a, b in zip(edges, edges[1:]) if b - a > 0.04]
        step = 0.25; frames = grey_frames(inp, crop=crop); act, diffs = motion_series(frames)
        still = still_stretches(diffs, step)
        onsets = new_elements(frames, act, step, hard)
        rep.update(hard_cuts=len(hard), hard_cuts_per_minute=per_min(len(hard)),
                   visual_changes=len(changes), visual_changes_per_minute=per_min(len(changes)),
                   new_elements_est=len(onsets), new_elements_per_minute_est=per_min(len(onsets)),
                   still_share=round(sum(1 for d in diffs if d < 0.6) / len(diffs), 3) if diffs else None,
                   still_stretches_over_3s=[{'seconds': round(s, 1), 'starts': stamp(a + off, True)}
                                            for s, a in sorted(still, reverse=True)[:10]],
                   shot_length_s={'median': round(statistics.median(shots), 2), 'shortest': round(min(shots), 2),
                                  'longest': round(max(shots), 2)} if shots else None,
                   hard_cut_times=[stamp(c + off, True) for c in hard],
                   new_element_times_est=[stamp(t + off, True) for t in onsets])
    if not has_audio:
        rep['audio'] = 'none: this file has no audio stream, so loudness and silence were skipped'
    else:
        lo = run(['ffmpeg', '-v', 'info', '-nostdin', *inp, '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'])
        mom = [(float(t), float(m)) for t, m in re.findall(r't:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+)', lo.stderr)]
        full = int(dur // 10) * 10
        per10 = {}
        for t, m in mom:
            if t < full:
                per10.setdefault(int(t // 10) * 10, []).append(m)
        summary = lo.stderr[lo.stderr.rfind('Summary:'):]
        num = lambda pat: (lambda f: float(f[0]) if f else None)(re.findall(pat, summary))
        rep['loudness'] = {'integrated_lufs': num(r'I:\s*(-?[\d.]+) LUFS'), 'lra_lu': num(r'LRA:\s*([\d.]+) LU'),
                           'true_peak_dbfs': num(r'Peak:\s*(-?[\d.]+) dBFS'),
                           'momentary_median_per_10s': {stamp(k + off): round(statistics.median(x), 1) for k, x in sorted(per10.items())}}
        if '--fine' in opts:
            per1 = {}
            for t, m in mom:
                per1.setdefault(int(t), []).append(m)
            rep['loudness']['momentary_max_per_1s'] = {stamp(k + off): round(max(x), 1) for k, x in sorted(per1.items())}
        si = run(['ffmpeg', '-v', 'info', '-nostdin', *inp, '-vn', '-af', 'silencedetect=n=-40dB:d=0.4', '-f', 'null', '-'])
        rep['silence_share'] = round(sum(float(x) for x in re.findall(r'silence_duration: ([\d.]+)', si.stderr)) / dur, 3) if dur else None
    rep['note'] = ('hard cuts = full-frame scene change > 0.30; visual changes = > 0.15; detections < 0.2 s apart count once. '
                   'new_elements_est = places where part of the picture changed and then stayed (8x6-block motion series), plus hard '
                   'cuts: an estimate of "something new appeared" (titles, cards, layout moves, cuts), within about 20 % of a count by '
                   'eye on two busy intros; misses changes in the first 0.5 s and tiny text; check the times on a sheet. still_share / still_stretches = frames with almost no pixel change (mean diff < 0.6/255 '
                   'on a 64x36 grey copy at 4 fps), which also catches eased motion. Jump cuts inside a small window can go uncounted; '
                   'check frames. silence_share is ~0 whenever a music bed runs under speech (use `pauses`). Numbers describe; they do not judge.'
                   + (' With crop, every picture measure is of that rectangle only (still resampled to 64x36 for the motion series); '
                      'a hard cut there can be a change inside the window. Loudness and silence are the whole mix.' if crop else ''))
    Path(out).write_text(json.dumps(rep, indent=1))
    keys = ('range', 'crop', 'duration_s', 'hard_cuts_per_minute', 'visual_changes_per_minute', 'new_elements_est', 'new_elements_per_minute_est',
            'still_share', 'still_stretches_over_3s', 'shot_length_s', 'audio')
    print(json.dumps({k: rep[k] for k in keys if k in rep}
                     | ({'loudness': {k: rep['loudness'][k] for k in ('integrated_lufs', 'lra_lu', 'true_peak_dbfs')}} if 'loudness' in rep else {}), indent=1))


WHISPER_WORDS = '''
import json, sys
from faster_whisper import WhisperModel
a = json.loads(sys.argv[1])
m = WhisperModel(a["model"], device="cpu", compute_type="int8")
res = []
for f in a["files"]:
    segs, info = m.transcribe(f, vad_filter=a["vad"], word_timestamps=True)
    res.append({"language": info.language, "words": [(w.start, w.end, w.word.strip()) for s in segs for w in s.words]})
json.dump(res, open(a["out"], "w"))
'''


def whisper_words(files, vad=True):
    """Word timestamps for each file (one model load). Returns [{'language', 'words': [(start, end, word)]}]."""
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / 'words.json'
        r = run([WHISPER_PY, '-c', WHISPER_WORDS, json.dumps({'model': WHISPER, 'files': [str(f) for f in files],
                                                                  'vad': vad, 'out': str(dst)})])
        if r.returncode:
            sys.exit(r.stderr[-2000:])
        return json.loads(dst.read_text())


def momentary(media):
    lo = run(['ffmpeg', '-v', 'info', '-nostdin', '-i', str(media), '-vn', '-af', 'ebur128', '-f', 'null', '-'])
    return [(float(t), float(m)) for t, m in re.findall(r't:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+)', lo.stderr)]


def cmd_pauses(media, out, *opts):
    """Pause = gap between words >= 0.6 s. Loudness from ebur128 momentary (400 ms window) at 0.1 s steps."""
    _, kw = parse(opts, ('--ranges',))
    dur = duration(media); off = offset_of(media)
    ranges = [(a, min(b, dur)) for a, b in (map(secs, r.split('-')) for r in kw['--ranges'].split(','))] if kw.get('--ranges') else [(0.0, dur)]
    mom = momentary(media)
    loud = lambda a, b: [m for t, m in mom if a + 0.4 <= t <= b]
    notes, per = [], []
    with tempfile.TemporaryDirectory() as tmp:
        cut = lambda i, a, b: wav16k(['-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', str(media)], f'{tmp}/r{i}-{a:.2f}.wav')
        files = [cut(i, a, b) for i, (a, b) in enumerate(ranges)] if kw.get('--ranges') else [str(media)]
        res = whisper_words(files)
        words = []
        for i, ((a, b), r) in enumerate(zip(ranges, res)):
            w = [(s + a, e + a, x) for s, e, x in r['words']]
            lvl = loud(a, b)
            speechy = lvl and sum(1 for m in lvl if m > -30) / len(lvl) > 0.5    # speech-level sound most of the time
            rate = lambda w: len(w) / ((b - a) / 60)
            if speechy and rate(w) < 30:
                tries = [('without VAD', a, whisper_words([files[i]], vad=False)[0]['words'])]
                if rate([(s + a, e + a, x) for s, e, x in tries[0][2]]) < 30 and b - a > 3:
                    tries.append(('starting 1 s later', a + 1, whisper_words([cut(f'{i}b', a + 1, b)])[0]['words']))
                best = max(tries, key=lambda t: len(t[2]))
                msg = (f'{stamp(a + off, True)}–{stamp(b + off, True)}: only {len(w)} words ({rate(w):.0f}/min) over speech-level sound; '
                       'retried ' + ', '.join(f'{t[0]} ({len(t[2])} words)' for t in tries))
                if len(best[2]) > len(w):
                    w = [(s + best[1], e + best[1], x) for s, e, x in best[2]]
                    msg += f'; using the {best[0]} result'
                if rate(w) < 30:
                    msg += '. STILL LOW: music, another language, or missed speech? Check by ear or with `transcribe`.'
                notes.append(msg)
            words.append(w)
            per.append({'range': f'{stamp(a + off, True)}–{stamp(b + off, True)}', 'words': len(w),
                        'words_per_minute_of_range': round(rate(w), 1)})
    gaps = [(b0, a1) for w in words for (_, b0, _), (a1, _, _) in zip(w, w[1:]) if a1 - b0 >= 0.6]
    allw = [x for w in words for x in w]
    spoken = sum(w[-1][1] - w[0][0] for w in words if w)
    in_speech = lambda t: any(a - 0.05 <= t - 0.4 and t <= b + 0.05 for a, b, _ in allw)
    in_pause = lambda t: any(a + 0.1 <= t - 0.4 and t <= b - 0.1 for a, b in gaps)
    inside = lambda t: any(a + 0.4 <= t <= b for a, b in ranges)
    sp = [m for t, m in mom if m > -70 and inside(t) and in_speech(t)]; pa = [m for t, m in mom if m > -70 and inside(t) and in_pause(t)]
    rep = {'file': str(media), 'source_offset_s': off, 'duration_s': round(sum(b - a for a, b in ranges), 2),
           'file_duration_s': round(dur, 2), 'words': len(allw),
           'words_per_minute': round(len(allw) / (spoken / 60), 1) if spoken else None,
           'pause_share_ge_0_6s': round(sum(b - a for a, b in gaps) / spoken, 3) if spoken else None,
           'pauses_ge_1s_per_minute': round(sum(1 for a, b in gaps if b - a >= 1) / (spoken / 60), 2) if spoken else None,
           'longest_pause': {'seconds': round(max((b - a for a, b in gaps), default=0), 2),
                             'at': stamp(max(gaps, key=lambda g: g[1] - g[0])[0] + off, True) if gaps else None},
           'speech_momentary_median_lufs': round(statistics.median(sp), 1) if sp else None,
           'pause_momentary_median_lufs': round(statistics.median(pa), 1) if pa else None,
           'pause_frames': len(pa)}
    if sp and pa:
        rep['bed_in_pauses_below_speech_LU'] = round(statistics.median(sp) - statistics.median(pa), 1)
    if kw.get('--ranges'):
        rep['ranges'] = per
    if notes:
        rep['warnings'] = notes
    rep['note'] = ('duration_s = the measured ranges\' total; file_duration_s = the whole file. '
                   'words_per_minute is over the spoken time (first to last word of each range). Mix-only: without stems the pause '
                   'level is the bed (music/atmos/SFX) plus room tone. Few pause frames = low confidence.')
    Path(out).write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    for n in notes:
        print('WARNING:', n, file=sys.stderr)


def cmd_transcribe(media, out, *opts):
    _, kw = parse(opts, ('--start', '--end'))
    s0, s1, inp = span_args(media, kw)
    with tempfile.TemporaryDirectory() as tmp:
        d = whisper_words([wav16k(inp, Path(tmp) / 'range.wav') if kw.get('--start') or kw.get('--end') else media])[0]
    off = offset_of(media) + s0
    lines, cur, start = [], [], None
    for a, b, word in d['words']:
        if start is None:
            start = a
        cur.append(word)
        if word.endswith(('.', '?', '!')) or len(cur) >= 14:
            lines.append(f'[{stamp(start + off, True)}] ' + ' '.join(cur)); cur, start = [], None
    if cur:
        lines.append(f'[{stamp(start + off, True)}] ' + ' '.join(cur))
    Path(out).write_text('\n'.join(lines) + '\n')
    written = [out]
    if '--words' in kw:
        wj = Path(out).with_suffix('.words.json')           # one word per line, so it greps
        head = json.dumps({'file': str(media), 'language': d['language'], 'times': 'source time, seconds'}, ensure_ascii=False)
        wj.write_text(head[:-1] + ', "words": [\n' + ',\n'.join(json.dumps(
            {'word': w, 'start': round(a + off, 2), 'end': round(b + off, 2)}, ensure_ascii=False) for a, b, w in d['words']) + '\n]}\n')
        written.append(wj)
    w0 = d['words'][0] if d['words'] else None
    first = (f"first word \"{w0[2]}\" at {stamp(w0[0] + off, True)} ({w0[0] + off:.2f} s, source time)" + (
        '; whisper pins a first word to the range start when sound starts with it, so it may be up to ~0.5 s later: check by ear'
        if w0[0] < 0.3 else '')) if w0 else 'no words'
    print('language', d['language'], len(d['words']), 'words →', ' + '.join(map(str, written)), '·', first)


def with_t(url, s):
    if 'youtu' not in url:
        return url
    return f"{url}{'&' if '?' in url else '?'}t={int(s)}s"


def hardlink(src, dst):
    """dst becomes another name for src (a copy only across drives)."""
    if dst.exists() and os.path.samefile(src, dst):
        return
    tmp = dst.with_name(dst.name + '.link-tmp')
    try:
        os.link(src, tmp)
    except OSError:
        shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def cmd_examples(spec, video, transcript, outroot, *opts):
    sp = json.loads(Path(spec).read_text())
    tactics = sp['tactics'] if 'tactics' in sp else sp
    meta_p = Path(transcript).parent / 'meta.json'
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    src = {'url': sidecar(video).get('url') or meta.get('webpage_url') or str(video),
           'title': f"{meta.get('channel')}, \"{meta.get('title')}\" ({(meta.get('upload_date') or '')[:4]})" if meta.get('title') else Path(video).stem,
           'captions': f"YouTube captions, {(meta.get('captions') or {}).get('type') or 'type unknown'}", 'prefix': meta.get('id') or Path(video).stem}
    src.update(sp.get('source', {}))
    man_p = Path(spec).with_suffix('.manifest.json')
    manifest = json.loads(man_p.read_text()) if man_p.exists() else {}
    done = manifest.setdefault('tactics', {})
    off, dur = offset_of(video), duration(video)
    lines = []
    for raw in Path(transcript).read_text().splitlines():
        m = re.match(r'\[([\d:.]+)\]', raw)
        if m:
            lines.append((secs(m.group(1)), raw))
    mmss = lambda s: f'{int(s // 60):02d}{int(s % 60):02d}'
    bad = []                                  # check the whole spec before writing anything
    for slug, t in tactics.items():
        for a, b, what in t.get('clips', []):
            if not 0 < secs(b) - secs(a) <= 20.05:
                bad.append(f'{slug}: clip {a}–{b} is not 0–20 s long')
        for x in [secs(f[0]) for f in t.get('frames', [])] + [secs(c[i]) for c in t.get('clips', []) for i in (0, 1)]:
            if not off - 0.01 <= x <= off + dur + 0.01:
                bad.append(f'{slug}: {stamp(x, True)} is outside the video ({stamp(off, True)}–{stamp(off + dur, True)})')
        for p, _ in t.get('copy', []):
            if not Path(p).exists():
                bad.append(f'{slug}: {p} does not exist')
    if bad:
        sys.exit('Spec problems, nothing written:\n  ' + '\n  '.join(bad))
    made = {}
    for slug, t in tactics.items():
        ex = Path(outroot) / slug / 'examples'
        mine = done.get(slug, {})
        foreign = sorted(p.name for p in (Path(outroot) / slug).rglob('*')
                         if p.is_file() and p.name not in mine.get('files', {}) and p.name != 'TACTIC.md') if (Path(outroot) / slug).exists() else []
        pre = mine['prefix'] if 'prefix' in mine else (src['prefix'].rstrip('-') + '-' if foreign else '')
        ex.mkdir(parents=True, exist_ok=True)
        files = {}

        def emit(name, key, make, what):
            dst = ex / f'{pre}{name}'
            if dst.exists() and dst.name not in mine.get('files', {}) and not any(dst == m for m in made.values()):
                sys.exit(f'{dst} exists and was not written by this spec; stopping rather than overwrite it.')
            if key in made:
                hardlink(made[key], dst); how = f'hardlink of {os.path.relpath(made[key], outroot)}'
            else:
                r = make(dst)
                if not dst.exists() or not dst.stat().st_size:
                    sys.exit(f'{dst}: not written. {getattr(r, "stderr", "")[-300:]}')
                made[key] = dst; how = 'written'
            files[dst.name] = {'what': what, 'how': how, 'bytes': dst.stat().st_size}

        ranges = [(secs(a), secs(b)) for a, b in t.get('transcript', [])]
        if ranges:
            body = [with_t(src['url'], ranges[0][0]),
                    f"{src['title']}. {src['captions']}, verbatim; [mm:ss] = source time. Excerpt: "
                    + ', '.join(f'{stamp(a)}–{stamp(b)}' for a, b in ranges) + '.', '']
            for i, (a, b) in enumerate(ranges):
                body += (['[...]'] if i else []) + [raw for s, raw in lines if a <= s <= b]
            emit('transcript.txt', ('transcript', tuple(ranges)), lambda d: d.write_text('\n'.join(body) + '\n'), 'transcript excerpt')
        for ts, what in t.get('frames', []):
            s = secs(ts)
            emit(f'{mmss(s)}-{what}.jpg', ('frame', round(s, 3)), lambda d, s=s: run(
                ['ffmpeg', '-v', 'error', '-y', '-ss', f'{s - off:.3f}', '-i', str(video), '-frames:v', '1', '-q:v', '2', str(d)]),
                f'frame at {stamp(s, True)}')
        for a, b, what in t.get('clips', []):
            a, b = secs(a), secs(b)
            emit(f'{mmss(a)}-{what}.mp4', ('clip', round(a, 3), round(b, 3)), lambda d, a=a, b=b: run(
                ['ffmpeg', '-v', 'error', '-y', '-ss', f'{a - off:.3f}', '-i', str(video), '-t', f'{b - a:.3f}', '-map', '0:v:0',
                 '-map', '0:a:0?', '-vf', "scale=-2:'min(1080,ih)'", '-c:v', 'libx264', '-preset', 'medium', '-crf', '26',
                 '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(d)]),
                f'clip {stamp(a, True)}–{stamp(b, True)}')
        for p, name in t.get('copy', []):
            key = ('copy', hashlib.sha256(Path(p).read_bytes()).hexdigest())
            made.setdefault(key, Path(p).resolve())       # an identical file is hardlinked, not copied
            emit(name, key, None, f'copy of {p}')
        done[slug] = {'prefix': pre, 'files': mine.get('files', {}) | files}
        manifest['source'] = src | {'video': str(video), 'transcript': str(transcript)}
        man_p.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))      # after every slug, so a re-run knows its files
        print(slug, f'(prefixed "{pre}": the folder already held {foreign})' if pre and not mine else '', sorted(files))
    print('manifest', man_p)


if __name__ == '__main__':
    cmds = {'fetch': cmd_fetch, 'segment': cmd_segment, 'frames': cmd_frames, 'sheet': cmd_sheet, 'analyze': cmd_analyze,
            'pauses': cmd_pauses, 'transcribe': cmd_transcribe, 'examples': cmd_examples}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](*sys.argv[2:])
