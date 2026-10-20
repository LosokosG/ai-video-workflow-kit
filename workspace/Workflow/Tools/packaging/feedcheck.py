#!/usr/bin/env python3
"""Thumbnail feed check: one PNG check sheet per candidate thumbnail, showing it the way viewers meet it.
PIL + stdlib; the `yt-dlp` CLI only for --ref-search (titles and thumbnail images, never videos).

  feedcheck.py CANDIDATE.png|jpg … --title "…" [--title "…" per candidate] --out DIR
               (--ref-search "niche query" [--n 11] | --refs DIR)
               [--channel NAME] [--position P] [--seed S] [--meta "1K views • 1 day ago"] [--duration 12:34]
               [--refresh]

Each sheet shows (a) a mock desktop home feed at real size: 4 columns of 360×202 tiles, the candidate among up to
11 reference thumbnails; (b) the same feed in greyscale; (c) a mobile feed column (390 px wide) and the watch-page
sidebar size (168×94); (d) the candidate alone at 320×180 with no title, plus greyscale and 160×90; (e) three proxy
numbers next to the references' values. With several candidates, feedcheck-compare.png shows them all at 320×180.
The candidate sits at the same random (or --position) slot on every sheet of a run, so candidates compare fairly.

--ref-search caches titles and thumbnails in ref-cache/<query-slug>/ (refs.json + <video id>.jpg) and reuses them
for 7 days (--refresh fetches again). --refs DIR takes any folder of 16:9 images; titles come from its refs.json
when present (so an earlier ref-cache folder works), else from the file names.
"""
import argparse, colorsys, datetime as dt, functools, hashlib, io, json, math, random, re, statistics, subprocess
import sys, time, unicodedata, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
REF_CACHE = HERE / 'ref-cache'
TODAY = dt.date.today()
CACHE_DAYS = 7

# YouTube dark theme (desktop web, 2025–26)
BG, CARD, TXT, SUB = (15, 15, 15), (39, 39, 39), (241, 241, 241), (170, 170, 170)
SHEET, LABEL, NOTE = (38, 38, 42), (255, 208, 64), (200, 200, 205)
TW, TH = 360, 202                    # desktop home tile
MW, MH = 390, 219                    # mobile full-width thumbnail
SW, SH = 168, 94                     # watch-page sidebar thumbnail
M = 40                               # sheet margin


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- text

FONT_DIRS = [Path('/usr/share/fonts'), Path.home() / '.local/share/fonts', Path.home() / '.fonts']
FONT_FILES = {  # first file found wins; Roboto is YouTube's face, Noto Sans the fallback
    'latin': {'regular': ['Roboto-Regular.ttf', 'NotoSans-Regular.ttf', 'DejaVuSans.ttf'],
              'medium': ['Roboto-Medium.ttf', 'NotoSans-Medium.ttf', 'DejaVuSans-Bold.ttf'],
              'bold': ['Roboto-Bold.ttf', 'NotoSans-Bold.ttf', 'DejaVuSans-Bold.ttf']},
    'cjk': {'regular': ['NotoSansCJK-Regular.ttc'], 'medium': ['NotoSansCJK-Medium.ttc'], 'bold': ['NotoSansCJK-Bold.ttc']},
    'deva': {'regular': ['NotoSansDevanagari-Regular.ttf'], 'medium': ['NotoSansDevanagari-Medium.ttf'],
             'bold': ['NotoSansDevanagari-Bold.ttf', 'NotoSansDevanagari-Medium.ttf']},
    'arab': {'regular': ['NotoSansArabic-Regular.ttf'], 'medium': ['NotoSansArabic-Medium.ttf'],
             'bold': ['NotoSansArabic-Bold.ttf', 'NotoSansArabic-Medium.ttf']},
    'thai': {'regular': ['NotoSansThai-Regular.ttf'], 'medium': ['NotoSansThai-Medium.ttf'],
             'bold': ['NotoSansThai-Bold.ttf', 'NotoSansThai-Medium.ttf']},
    'math': {w: ['NotoSansMath-Regular.ttf', 'DejaVuSans.ttf'] for w in ('regular', 'medium', 'bold')},
}


@functools.lru_cache(None)
def font_file(script, weight):
    for name in FONT_FILES.get(script, {}).get(weight, []):
        for d in FONT_DIRS:
            if d.exists() and (hit := next(d.rglob(name), None)):
                return str(hit)
    return None if script != 'latin' else subprocess.run(
        ['fc-match', '-f', '%{file}', f'sans:{weight}'], capture_output=True, text=True).stdout.strip() or None


@functools.lru_cache(None)
def font(script, weight, size):
    path = font_file(script, weight) or font_file('latin', weight)
    return ImageFont.truetype(path, size) if path else ImageFont.load_default(size)


def script_of(ch):
    o = ord(ch)
    if 0x3040 <= o <= 0x30FF or 0x3400 <= o <= 0x9FFF or 0xAC00 <= o <= 0xD7AF or 0xFF00 <= o <= 0xFFEF:
        return 'cjk'
    if 0x0900 <= o <= 0x097F:
        return 'deva'
    if 0x0600 <= o <= 0x06FF:
        return 'arab'
    if 0x0E00 <= o <= 0x0E7F:
        return 'thai'
    if 0x2190 <= o <= 0x22FF or 0x27F0 <= o <= 0x27FF or 0x2A00 <= o <= 0x2AFF:   # arrows, ≥ ≤ ≈ etc.
        return 'math'
    return 'latin'


def clean(text):
    """Drop emoji and pictographs (no colour-emoji rendering here) and collapse spaces."""
    text = ''.join(c for c in (text or '') if unicodedata.category(c) not in ('So', 'Cs', 'Co', 'Cn', 'Cf'))
    return re.sub(r'\s+', ' ', text.replace('⃣', '')).strip()


def runs(text, weight, size):
    out, cur, buf = [], None, ''
    for ch in text:
        key = cur if (ch == ' ' and cur) else script_of(ch)
        if key != cur and buf:
            out.append((buf, font(cur, weight, size)))
            buf = ''
        cur, buf = key, buf + ch
    if buf:
        out.append((buf, font(cur, weight, size)))
    return out


def tw(text, weight, size):
    return sum(f.getlength(s) for s, f in runs(text, weight, size))


def dtext(draw, x, top, text, weight, size, fill, line_h=None):
    """Draw one line with its baseline centred in a line box of line_h starting at `top`."""
    line_h = line_h or round(size * 1.4)
    base = top + round((line_h + size * 0.72) / 2)
    for s, f in runs(text, weight, size):
        draw.text((x, base), s, font=f, fill=fill, anchor='ls')
        x += f.getlength(s)


def wrap(text, weight, size, width, max_lines):
    toks = re.findall(r'[぀-ヿ㐀-鿿가-힯]|[^\s぀-ヿ㐀-鿿가-힯]+\s*|\s+',
                      text)
    lines, cur = [], ''
    for tok in toks:
        if tw((cur + tok).rstrip(), weight, size) <= width:
            cur += tok
            continue
        if cur.strip():
            lines.append(cur.rstrip())
        cur = tok.lstrip()
        while tw(cur.rstrip(), weight, size) > width:     # a single word wider than the line
            k = len(cur)
            while k > 1 and tw(cur[:k], weight, size) > width:
                k -= 1
            lines.append(cur[:k])
            cur = cur[k:]
    if cur.strip():
        lines.append(cur.rstrip())
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        while last and tw(last.rstrip() + '…', weight, size) > width:
            last = last[:-1]
        lines = lines[:max_lines - 1] + [last.rstrip(' ,.:;-–—|') + '…']
    return lines


# ---------------------------------------------------------------- shapes

@functools.lru_cache(None)
def round_mask(w, h, r):
    s = 4
    m = Image.new('L', (w * s, h * s), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=255)
    return m.resize((w, h), Image.LANCZOS)


@functools.lru_cache(None)
def circle_mask(d):
    s = 4
    m = Image.new('L', (d * s, d * s), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * s - 1, d * s - 1), fill=255)
    return m.resize((d, d), Image.LANCZOS)


def paste_thumb(canvas, img, x, y, w, h, radius):
    t = img.resize((w, h), Image.LANCZOS)
    canvas.paste(t, (x, y), round_mask(w, h, radius) if radius else None)


def badge(canvas, text, right, bottom, size=12):
    """Duration badge: dark translucent rounded box in the thumbnail's bottom-right corner."""
    if not text:
        return
    w = math.ceil(tw(text, 'medium', size)) + 8
    h = size + 6
    box = (right - w, bottom - h, right, bottom)
    region = canvas.crop(box)
    dark = Image.blend(region, Image.new('RGB', region.size, (0, 0, 0)), 0.8)
    canvas.paste(dark, box[:2], round_mask(w, h, 4))
    dtext(ImageDraw.Draw(canvas), box[0] + 4, box[1], text, 'medium', size, (255, 255, 255), line_h=h)


def avatar(canvas, name, x, y, d=36):
    hsh = int(hashlib.md5((name or '?').encode()).hexdigest()[:6], 16)
    r, g, b = colorsys.hls_to_rgb((hsh % 360) / 360, 0.42, 0.45)
    disc = Image.new('RGB', (d, d), (int(r * 255), int(g * 255), int(b * 255)))
    canvas.paste(disc, (x, y), circle_mask(d))
    initial = (clean(name) or '?')[0].upper()
    size = round(d * 0.45)
    dtext(ImageDraw.Draw(canvas), x + (d - tw(initial, 'medium', size)) / 2, y, initial, 'medium', size,
          (255, 255, 255), line_h=d)


def chips(canvas, x, y, width, labels):
    draw = ImageDraw.Draw(canvas)
    for i, lab in enumerate(labels):
        w = math.ceil(tw(lab, 'medium', 14)) + 24
        if x + w > width:
            break
        fill, col = ((241, 241, 241), (15, 15, 15)) if i == 0 else (CARD, TXT)
        draw.rounded_rectangle((x, y, x + w, y + 32), 8, fill=fill)
        dtext(draw, x + 12, y, lab, 'medium', 14, col, line_h=32)
        x += w + 12


# ---------------------------------------------------------------- reference thumbnails

def to_16x9(img):
    img = img.convert('RGB')
    w, h = img.size
    if abs(w / h - 16 / 9) < 0.02:
        return img
    if w / h < 16 / 9:     # 4:3 frames (hqdefault/sddefault) letterbox a 16:9 picture: keep the middle band
        bh = round(w * 9 / 16)
        return img.crop((0, (h - bh) // 2, w, (h - bh) // 2 + bh))
    bw = round(h * 16 / 9)
    return img.crop(((w - bw) // 2, 0, (w - bw) // 2 + bw, h))


def slug(q):
    return re.sub(r'[^a-z0-9]+', '-', q.lower()).strip('-')[:60] or 'refs'


def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def ytdlp_search(query, n):
    cmd = ['yt-dlp', '--flat-playlist', '-J', '--no-warnings', '--extractor-retries', '1',
           '--extractor-args', 'youtubetab:approximate_date', f'ytsearch{n}:{query}']
    for attempt in (1, 2):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
        err = (r.stderr or '').strip()
        if attempt == 1 and re.search(r'HTTP Error (429|403)|Too Many Requests|not a bot', err, re.I):
            log('  YouTube refused the request (429/403); waiting 60 s and retrying once…')
            time.sleep(60)
            continue
        sys.exit(f'yt-dlp search failed: {err.splitlines()[-1] if err else "no output"}')


def fetch_refs(query, n, refresh):
    d = REF_CACHE / slug(query)
    meta = d / 'refs.json'
    if meta.exists() and not refresh:
        data = json.loads(meta.read_text())
        age = (TODAY - dt.date.fromisoformat(data['fetched'])).days
        if age <= CACHE_DAYS and len(data['items']) >= n:
            log(f'Using cached references for "{query}" (fetched {data["fetched"]}): {d}')
            return d, data
    log(f'Searching YouTube for "{query}" (one yt-dlp call; titles and thumbnails only)…')
    entries = ytdlp_search(query, n + 6).get('entries') or []
    d.mkdir(parents=True, exist_ok=True)
    items = []
    for e in entries:
        if len(items) >= n:
            break
        vid = e.get('id')
        if not vid or '/shorts/' in (e.get('url') or '') or e.get('live_status') in ('is_live', 'is_upcoming'):
            continue
        dest = d / f'{vid}.jpg'
        if not dest.exists():
            for url in (f'https://i.ytimg.com/vi/{vid}/{name}.jpg'
                        for name in ('hq720', 'maxresdefault', 'sddefault', 'hqdefault')):
                try:
                    raw = http_get(url)
                    img = Image.open(io.BytesIO(raw))
                    if img.width < 320:
                        continue
                    to_16x9(img).save(dest, quality=92)
                    break
                except Exception:
                    continue
            time.sleep(0.3)
        if not dest.exists():
            log(f'  no thumbnail for {vid}; skipped')
            continue
        items.append({'id': vid, 'file': dest.name, 'title': e.get('title') or '', 'channel': e.get('channel') or '',
                      'views': e.get('view_count'), 'duration': e.get('duration'), 'ts': e.get('timestamp')})
    data = {'query': query, 'fetched': TODAY.isoformat(), 'source': 'YouTube search via yt-dlp --flat-playlist',
            'items': items}
    meta.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    log(f'  saved {len(items)} thumbnails to {d}')
    return d, data


def load_refs_dir(d, n):
    d = Path(d)
    meta = d / 'refs.json'
    if meta.exists():
        data = json.loads(meta.read_text())
        data['items'] = [it for it in data['items'] if (d / it['file']).exists()]
    else:
        files = sorted(p for p in d.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'))
        data = {'query': None, 'fetched': None, 'items': [
            {'file': p.name, 'title': re.sub(r'[_-]+', ' ', p.stem), 'channel': 'Reference', 'views': None,
             'duration': None, 'ts': None} for p in files]}
    data['items'] = data['items'][:n]
    return d, data


# ---------------------------------------------------------------- display strings

def compact(n):
    for div, suf in ((1e9, 'B'), (1e6, 'M'), (1e3, 'K')):
        if n >= div:
            x = n / div
            return (f'{x:.1f}'.rstrip('0').rstrip('.') if x < 10 else f'{x:.0f}') + suf
    return str(int(n))


def ago(ts):
    if not ts:
        return ''
    d = (time.time() - ts) / 86400
    for limit, unit, div in ((1, 'hour', 1 / 24), (7, 'day', 1), (31, 'week', 7), (365, 'month', 30.4),
                             (1e9, 'year', 365.25)):
        if d < limit:
            k = max(1, round(d / div))
            return f'{k} {unit}{"s" * (k != 1)} ago'


def dur(sec):
    if not sec:
        return ''
    sec = int(sec)
    return f'{sec // 3600}:{sec // 60 % 60:02d}:{sec % 60:02d}' if sec >= 3600 else f'{sec // 60}:{sec % 60:02d}'


def meta_line(it):
    parts = ([f'{compact(it["views"])} views'] if it.get('views') is not None else []) + ([ago(it['ts'])] if it.get('ts') else [])
    return ' • '.join(parts)


# ---------------------------------------------------------------- panels

ROW_PITCH = TH + 12 + 44 + 40 + 36    # thumb, gap, 2-line title, channel + meta lines, row gap
CHIP_LABELS = ['All', 'AI', 'Programming', 'Podcasts', 'Music', 'Gaming', 'Live', 'Computers', 'Recently uploaded',
               'Watched', 'New to you']


def desktop_feed(items):
    cols = 4
    rows = math.ceil(len(items) / cols)
    W = 24 + cols * TW + (cols - 1) * 16 + 24
    H = 24 + 32 + 24 + rows * ROW_PITCH - 36 + 8
    img = Image.new('RGB', (W, H), BG)
    chips(img, 24, 24, W - 24, CHIP_LABELS)
    draw = ImageDraw.Draw(img)
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x, y = 24 + c * (TW + 16), 24 + 32 + 24 + r * ROW_PITCH
        paste_thumb(img, it['img'], x, y, TW, TH, 12)
        badge(img, it['duration'], x + TW - 6, y + TH - 6)
        ty = y + TH + 12
        avatar(img, it['channel'], x, ty)
        for k, line in enumerate(wrap(it['title'], 'medium', 16, TW - 48 - 24, 2)):
            dtext(draw, x + 48, ty + 22 * k, line, 'medium', 16, TXT, 22)
        ty += 22 * len(wrap(it['title'], 'medium', 16, TW - 48 - 24, 2))
        for text in (it['channel'], it['meta']):
            if text:
                dtext(draw, x + 48, ty + 2, (wrap(text, 'regular', 14, TW - 48 - 24, 1) or [''])[0], 'regular', 14,
                      SUB, 20)
                ty += 20
    return img


def mobile_feed(items, height=844):
    img = Image.new('RGB', (MW, height), BG)
    draw = ImageDraw.Draw(img)
    # app bar and chip row (placeholders, no logos)
    draw.rounded_rectangle((12, 14, 100, 34), 4, fill=(60, 60, 60))
    for k in range(3):
        draw.ellipse((MW - 40 - k * 40, 12, MW - 16 - k * 40, 36), fill=(60, 60, 60))
    chips(img, 12, 56, MW, CHIP_LABELS[:5])
    y = 100
    for it in items:
        if y >= height - 56:
            break
        paste_thumb(img, it['img'], 0, y, MW, MH, 0)
        badge(img, it['duration'], MW - 8, y + MH - 8)
        ty = y + MH + 12
        avatar(img, it['channel'], 12, ty)
        lines = wrap(it['title'], 'medium', 15, MW - 60 - 40, 2)
        for k, line in enumerate(lines):
            dtext(draw, 60, ty + 20 * k, line, 'medium', 15, TXT, 20)
        ty += 20 * len(lines)
        sub = ' · '.join(p for p in (it['channel'], it['meta'].replace(' • ', ' · ')) if p)
        dtext(draw, 60, ty + 2, (wrap(sub, 'regular', 12, MW - 60 - 40, 1) or [''])[0], 'regular', 12, SUB, 18)
        y = ty + 20 + 24
    # bottom navigation bar (placeholder icons)
    draw.rectangle((0, height - 56, MW, height), fill=BG)
    draw.line((0, height - 56, MW, height - 56), fill=(48, 48, 48))
    for k in range(5):
        cx = MW * (2 * k + 1) // 10
        draw.ellipse((cx - 11, height - 44, cx + 11, height - 22), outline=(120, 120, 120), width=2)
    return img


def sidebar(items):
    W = 402
    pitch = SH + 8
    img = Image.new('RGB', (W, len(items) * pitch + 8), BG)
    draw = ImageDraw.Draw(img)
    for i, it in enumerate(items):
        y = 8 + i * pitch
        paste_thumb(img, it['img'], 0, y, SW, SH, 8)
        badge(img, it['duration'], SW - 4, y + SH - 4, 11)
        lines = wrap(it['title'], 'medium', 14, W - SW - 8 - 24, 2)
        for k, line in enumerate(lines):
            dtext(draw, SW + 8, y + 20 * k, line, 'medium', 14, TXT, 20)
        ty = y + 20 * len(lines) + 2
        for text in (it['channel'], it['meta']):
            if text:
                dtext(draw, SW + 8, ty, (wrap(text, 'regular', 12, W - SW - 8 - 24, 1) or [''])[0], 'regular', 12,
                      SUB, 18)
                ty += 18
    return img


# ---------------------------------------------------------------- proxy metrics

_LIN = [(i / 255 / 12.92) if i / 255 <= 0.04045 else ((i / 255 + 0.055) / 1.055) ** 2.4 for i in range(256)]


def _lstar(y):
    return 116 * y ** (1 / 3) - 16 if y > 216 / 24389 else y * 24389 / 27


EDGE_T = 32    # Sobel magnitude on 8-bit luma: a local step of ~8 grey levels. 128 missed faint clutter entirely.


def flat(im):
    return im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()


def metrics(img):
    """Measured at 320×180, the size the checks are about."""
    im = img.convert('RGB').resize((320, 180), Image.LANCZOS)
    W, H = im.size
    px = list(flat(im))
    L = [_lstar(0.2126 * _LIN[r] + 0.7152 * _LIN[g] + 0.0722 * _LIN[b]) for r, g, b in px]
    bx, by = W // 8, H // 8
    centre = [L[y * W + x] for y in range(H // 4, 3 * H // 4) for x in range(W // 4, 3 * W // 4)]
    border = [L[y * W + x] for y in range(H) for x in range(W) if x < bx or x >= W - bx or y < by or y >= H - by]
    dl = statistics.fmean(centre) - statistics.fmean(border)
    rg = [r - g for r, g, b in px]
    yb = [(r + g) / 2 - b for r, g, b in px]
    colourful = (math.hypot(statistics.pstdev(rg), statistics.pstdev(yb))
                 + 0.3 * math.hypot(statistics.fmean(rg), statistics.fmean(yb)))
    g = list(flat(im.convert('L')))
    edges, t2 = 0, EDGE_T * EDGE_T
    for y in range(1, H - 1):
        a, b, c = (y - 1) * W, y * W, (y + 1) * W
        for x in range(1, W - 1):
            gx = (g[a + x + 1] + 2 * g[b + x + 1] + g[c + x + 1]) - (g[a + x - 1] + 2 * g[b + x - 1] + g[c + x - 1])
            gy = (g[c + x - 1] + 2 * g[c + x] + g[c + x + 1]) - (g[a + x - 1] + 2 * g[a + x] + g[a + x + 1])
            if gx * gx + gy * gy >= t2:
                edges += 1
    return {'contrast': abs(dl), 'centre_brighter': dl >= 0, 'colour': colourful,
            'edges': 100 * edges / ((W - 2) * (H - 2))}


COLOUR_BANDS = [(0, 'not colourful'), (15, 'slightly colourful'), (33, 'moderately colourful'),
                (45, 'averagely colourful'), (59, 'quite colourful'), (82, 'highly colourful'),
                (109, 'extremely colourful')]


def colour_band(v):
    return [name for lim, name in COLOUR_BANDS if v >= lim][-1]


# ---------------------------------------------------------------- sheet

def label(draw, x, y, head, sub=''):
    dtext(draw, x, y, head, 'bold', 18, LABEL, 26)
    if sub:
        dtext(draw, x + tw(head, 'bold', 18) + 12, y + 1, sub, 'regular', 15, NOTE, 26)


def candidate_checks(path, img):
    size = path.stat().st_size
    w, h = img.size
    out = [f'{w}×{h} {img.format or path.suffix.upper().lstrip(".")}, {size / 1e6:.2f} MB']
    out.append('16:9 ok' if abs(w / h - 16 / 9) < 0.01 else
               'NOT 16:9: YouTube adds black bars (shown here the same way; they count as border in ΔL*)')
    out.append('≥ 640 px wide ok' if w >= 640 else 'UNDER 640 px wide: YouTube rejects it')
    out.append('≤ 2 MB ok for a mobile upload' if size <= 2e6 else 'over 2 MB: desktop upload only (≤ 50 MB)')
    if path.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
        out.append('YouTube takes JPG or PNG only')
    return out


def letterbox(img):
    img = img.convert('RGBA') if img.mode in ('RGBA', 'LA', 'P') else img.convert('RGB')
    if img.mode == 'RGBA':
        base = Image.new('RGB', img.size, (0, 0, 0))
        base.paste(img, mask=img.getchannel('A'))
        img = base
    w, h = img.size
    if abs(w / h - 16 / 9) < 0.01:
        return img
    W, H = (w, round(w * 9 / 16)) if w / h > 16 / 9 else (round(h * 16 / 9), h)
    out = Image.new('RGB', (W, H), (0, 0, 0))
    out.paste(img, ((W - w) // 2, (H - h) // 2))
    return out


def build_sheet(cand, refs, pos, ref_note, ref_metrics):
    items = [dict(r) for r in refs]
    items.insert(pos - 1, cand)
    feed = desktop_feed(items)
    grey = ImageOps.grayscale(feed).convert('RGB')
    mob = mobile_feed([cand] + refs[:3])
    side = sidebar(refs[:2] + [cand] + refs[2:4])
    cm = cand['metrics']

    W = M + feed.width + M + grey.width + M
    top = 150
    rowb_y = top + 34 + feed.height + 56
    H = rowb_y + 34 + mob.height + M
    sheet = Image.new('RGB', (W, H), SHEET)
    draw = ImageDraw.Draw(sheet)

    # header
    dtext(draw, M, 24, f'Feed check · {cand["path"].name}', 'bold', 28, (255, 255, 255), 40)
    dtext(draw, M, 66, f'Title: "{cand["title_raw"]}"   ·   Channel: {cand["channel"]}   ·   {ref_note}', 'regular',
          17, NOTE, 26)
    dtext(draw, M, 94, 'Real size in CSS pixels: view at 100 % (200 % on a 2× display). First, glance at (a) for one '
          'second: where does your eye land? Then read the rest.', 'regular', 17, NOTE, 26)

    # row A: colour and greyscale feeds
    label(draw, M, top, '(a) Desktop home feed', f'360×202 tiles, real size · win-the-first-glance')
    sheet.paste(feed, (M, top + 34))
    gx = M + feed.width + M
    label(draw, gx, top, '(b) Same feed in greyscale', 'brightness-contrast: does the subject still separate?')
    sheet.paste(grey, (gx, top + 34))

    # row B: mobile, sidebar, candidate alone, numbers
    x = M
    label(draw, x, rowb_y, '(c) Mobile feed', '390 px wide')
    sheet.paste(mob, (x, rowb_y + 34))
    x += mob.width + M
    label(draw, x, rowb_y, 'Watch-page sidebar', '168×94')
    sheet.paste(side, (x, rowb_y + 34))
    x += side.width + M
    label(draw, x, rowb_y, '(d) Alone, no title', '320×180')
    y = rowb_y + 34
    alone = cand['img'].resize((320, 180), Image.LANCZOS)
    sheet.paste(alone, (x, y))
    dtext(draw, x, y + 184, 'No title: what is this video about?', 'regular', 14, NOTE, 20)
    y += 180 + 40
    sheet.paste(ImageOps.grayscale(alone).convert('RGB'), (x, y))
    dtext(draw, x, y + 184, 'Greyscale: subject separated?', 'regular', 14, NOTE, 20)
    y += 180 + 40
    sheet.paste(cand['img'].resize((160, 90), Image.LANCZOS), (x, y))
    dtext(draw, x + 172, y + 20, '160×90: sum it up', 'regular', 14, NOTE, 20)
    dtext(draw, x + 172, y + 42, 'in five words?', 'regular', 14, NOTE, 20)

    # (e) numbers
    x += 320 + M + 20
    label(draw, x, rowb_y, '(e) Proxy numbers', 'crude measurements at 320×180: prompts for your eye, not verdicts')
    y = rowb_y + 34 + 8
    n = len(ref_metrics)
    cols = [x, x + 330, x + 520, x + 860]
    for cx, head in zip(cols, ['Measure', 'Candidate', f'References (n={n}): median, range', 'Candidate vs refs']):
        dtext(draw, cx, y, head, 'bold', 16, TXT, 24)
    y += 34
    rows = [
        ('contrast', 'Centre vs border ΔL*', lambda v: f'{v:.0f}',
         'centre and border about equal' if cm['contrast'] < 3 else
         'centre ' + ('brighter' if cm['centre_brighter'] else 'darker') + ' than border', 'more separated than'),
        ('colour', 'Colourfulness (Hasler–Süsstrunk)', lambda v: f'{v:.0f}', colour_band(cm['colour']),
         'more colourful than'),
        ('edges', 'Edge density ("clutter")', lambda v: f'{v:.1f} %', 'lower = simpler', 'busier than'),
    ]
    for key, name, fmt, note, verb in rows:
        vals = [m[key] for m in ref_metrics]
        v = cm[key]
        dtext(draw, cols[0], y, name, 'medium', 16, TXT, 24)
        dtext(draw, cols[1], y, fmt(v), 'bold', 18, (255, 255, 255), 24)
        if vals:
            dtext(draw, cols[2], y, f'{fmt(statistics.median(vals))}   ({fmt(min(vals))} – {fmt(max(vals))})',
                  'regular', 16, TXT, 24)
            below = sum(1 for r in vals if r < v)
            dtext(draw, cols[3], y, f'{verb} {below} of {n}', 'regular', 16, TXT, 24)
        dtext(draw, cols[1], y + 24, note, 'regular', 13, SUB, 20)
        y += 60
    y += 6
    expl = [
        'Centre vs border ΔL*: mean CIE lightness (0–100) of the middle 50 % × 50 % box minus the outer 12.5 % frame.',
        'A crude stand-in for "does the subject stand off the background"; it assumes a centred subject, and a face',
        'on the left or right third, or a bright border, fools it. Use (b) and the greyscale 320×180 to judge.',
        'Colourfulness: Hasler & Süsstrunk (2003) M = σ(rg, yb) + 0.3·μ(rg, yb). ~15 slightly, ~33 moderately,',
        '~45 averagely, ~59 quite, ~82 highly colourful. Says nothing about ONE accent vs a rainbow (colour-contrast).',
        f'Edge density: share of pixels whose Sobel gradient on 8-bit luma is ≥ {EDGE_T} (a local step of ~8 grey levels).',
        'Text, UI screenshots, textured faces and busy backgrounds raise it; a clean subject on a plain ground lowers it.',
        'Very faint detail blurs away at this size and barely counts, even when the full-size image looks busy.',
    ]
    for line in expl:
        dtext(draw, x, y, line, 'regular', 14, NOTE, 21)
        y += 21
    y += 14
    dtext(draw, x, y, 'Upload checks', 'bold', 16, TXT, 24)
    y += 26
    for line in cand['checks']:
        dtext(draw, x, y, '· ' + line, 'regular', 14, NOTE, 21)
        y += 21
    y += 14
    r, c = divmod(pos - 1, 4)
    dtext(draw, x, y, f'Where the candidate sits: (a) row {r + 1}, column {c + 1} (slot {pos}); (c) first item; '
          f'sidebar third item.', 'regular', 14, NOTE, 21)
    y += 21
    dtext(draw, x, y, f'Tactic checks: Workflow/Tactics/titles-thumbnails/ (win-the-first-glance, brightness-contrast, '
          f'colour-contrast, one-second-simple, thumbnail-works-before-title).', 'regular', 14, NOTE, 21)
    return sheet


def compare_sheet(cands):
    n = len(cands)
    W = M + n * 320 + (n - 1) * 32 + M
    H = 90 + 30 + 180 + 24 + 180 + 24 + 90 + 110 + M
    sheet = Image.new('RGB', (W, H), SHEET)
    draw = ImageDraw.Draw(sheet)
    dtext(draw, M, 20, 'Candidates side by side · 320×180, no titles', 'bold', 24, (255, 255, 255), 34)
    dtext(draw, M, 56, 'Top row colour, then greyscale, then 160×90. Numbers are proxies (see each sheet).',
          'regular', 15, NOTE, 22)
    for i, c in enumerate(cands):
        x, y = M + i * (320 + 32), 90
        dtext(draw, x, y, (wrap(c['path'].name, 'bold', 16, 320, 1) or [''])[0], 'bold', 16, LABEL, 26)
        y += 30
        small = c['img'].resize((320, 180), Image.LANCZOS)
        sheet.paste(small, (x, y))
        y += 180 + 24
        sheet.paste(ImageOps.grayscale(small).convert('RGB'), (x, y))
        y += 180 + 24
        sheet.paste(c['img'].resize((160, 90), Image.LANCZOS), (x, y))
        y += 90 + 14
        m = c['metrics']
        for line in (f'Centre vs border ΔL*: {m["contrast"]:.0f}', f'Colourfulness: {m["colour"]:.0f}',
                     f'Edge density: {m["edges"]:.1f} %'):
            dtext(draw, x, y, line, 'regular', 15, TXT, 22)
            y += 24
    return sheet


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('candidates', nargs='+', type=Path, metavar='CANDIDATE')
    ap.add_argument('--title', action='append', required=True,
                    help='the video title; once for all candidates, or once per candidate in order')
    ap.add_argument('--channel', default='Your channel', help='channel name shown under the candidate')
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--refs', type=Path, metavar='DIR', help='folder of reference thumbnails')
    src.add_argument('--ref-search', metavar='QUERY', help='fetch current thumbnails for a niche YouTube search')
    ap.add_argument('--n', type=int, default=11, help='reference thumbnails (max 11, default 11)')
    ap.add_argument('--out', type=Path, required=True, metavar='DIR')
    ap.add_argument('--position', type=int, help='candidate slot in the desktop grid, 1–12 (default random)')
    ap.add_argument('--seed', type=int, help='seed for the random slot')
    ap.add_argument('--meta', default='1K views • 1 day ago', help='the candidate\'s views/age line')
    ap.add_argument('--duration', default='12:34', help='the candidate\'s duration badge')
    ap.add_argument('--refresh', action='store_true', help='fetch the --ref-search thumbnails again')
    args = ap.parse_args()

    n = max(1, min(args.n, 11))
    if len(args.title) not in (1, len(args.candidates)):
        sys.exit('Give --title once, or once per candidate.')
    for p in args.candidates:
        if not p.exists():
            sys.exit(f'No such file: {p}')

    ref_dir, data = fetch_refs(args.ref_search, n, args.refresh) if args.ref_search else load_refs_dir(args.refs, n)
    if not data['items']:
        sys.exit(f'No reference thumbnails in {ref_dir}')
    refs = []
    for it in data['items'][:n]:
        refs.append({'img': to_16x9(Image.open(ref_dir / it['file'])), 'title': clean(it['title']),
                     'channel': clean(it.get('channel') or ''), 'meta': meta_line(it), 'duration': dur(it.get('duration'))})
    log(f'Measuring {len(refs)} reference thumbnails…')
    ref_metrics = [metrics(r['img']) for r in refs]
    if data.get('query'):
        ref_note = f'References: {len(refs)} from YouTube search "{data["query"]}" (fetched {data["fetched"]})'
    else:
        ref_note = f'References: {len(refs)} from {ref_dir}'

    rng = random.Random(args.seed)
    pos = args.position or rng.randint(1, len(refs) + 1)
    pos = max(1, min(pos, len(refs) + 1))
    args.out.mkdir(parents=True, exist_ok=True)
    cands = []
    for i, p in enumerate(args.candidates):
        raw = Image.open(p)
        raw.load()
        img = letterbox(raw)
        title = args.title[i] if len(args.title) > 1 else args.title[0]
        cand = {'path': p, 'img': img, 'title': clean(title), 'title_raw': title, 'channel': args.channel,
                'meta': args.meta, 'duration': args.duration, 'checks': candidate_checks(p, raw),
                'metrics': metrics(img)}
        cands.append(cand)
        out = args.out / f'feedcheck-{p.stem}.png'
        build_sheet(cand, refs, pos, ref_note, ref_metrics).save(out)
        log(f'Wrote {out}')
    if len(cands) > 1:
        out = args.out / 'feedcheck-compare.png'
        compare_sheet(cands).save(out)
        log(f'Wrote {out}')


if __name__ == '__main__':
    main()
