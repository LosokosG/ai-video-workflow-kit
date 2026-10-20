#!/usr/bin/env python3
"""Outlier finder: a video's views ÷ its channel's median views, from yt-dlp flat listings.
No login, no downloads, no paid service. Stdlib only; needs the `yt-dlp` CLI.

  outliers.py channels URL_OR_@HANDLE… [--latest N | --popular] [--out FILE.md]
      Per channel, from the long-form videos tab (Shorts and live streams excluded): the median views and the
      top 15 by score. Default window: the latest 60 uploads (AI moves fast; all-time lists go stale).
      --popular: the all-time view, i.e. every upload (up to --latest, default 1000 then) sorted by views.
      With several channels, also the top 15 by views and by score across them, with subscriber counts.
  outliers.py search "phrase"… [--n 20] [--min-views V] [--min-median M] [--max-channels K] [--out FILE.md]
      Desire-phrase search: ytsearchN per phrase, look up each result channel's median (the most-viewed results'
      channels first, at most K fresh lookups per run), rank by score, with subscriber counts.
  outliers.py exists "title" ["variation"…] [--n 10] [--out FILE.md]
      Originality search: the top results for the title and each variation, with views and channel.

Output is markdown on stdout. --out FILE.md writes a new file instead (parent folders are created; an existing
file is never changed: a -2, -3… suffix is added), e.g. Workflow/Ideas-Research/<YYYY-MM-DD>-<topic>.md.
Channel listings are cached in cache/channels.json: `channels` reuses a listing fetched today, `search` reuses
medians up to --cache-days old. --refresh ignores the cache. Progress and the yt-dlp call count go to stderr.
"""
import argparse, datetime as dt, json, random, re, shlex, statistics, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / 'cache' / 'channels.json'
TODAY = dt.date.today()
NEW_DAYS = 30              # uploads younger than this are still gaining views
TINY_MEDIAN = 1000         # below this, scores mostly reflect promotion, not the idea
LATEST_DEFAULT = 60        # channels: default window, latest uploads
POPULAR_DEFAULT = 1000     # channels --popular: cap on uploads listed (30 per page request)
LOOKUP_SLEEP = (2.0, 4.0)  # seconds between channel lookups and between searches
CALLS = 0


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- yt-dlp

def ytdlp_flat(target, playlist_end=None):
    """One `yt-dlp --flat-playlist -J` call. Retries once after 60 s when YouTube refuses (429/403/bot check)."""
    global CALLS
    cmd = ['yt-dlp', '--flat-playlist', '-J', '--no-warnings', '--extractor-retries', '1', '--sleep-requests', '1',
           '--extractor-args', 'youtubetab:approximate_date']
    if playlist_end:
        cmd += ['--playlist-end', str(playlist_end)]
    cmd.append(target)
    for attempt in (1, 2):
        CALLS += 1
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
        err = (r.stderr or '').strip()
        refused = re.search(r'HTTP Error (429|403)|Too Many Requests|not a bot|rate.?limit', err, re.I)
        if refused and attempt == 1:
            log(f'  YouTube refused the request ({refused.group(0)}); waiting 60 s and retrying once…')
            time.sleep(60)
            continue
        raise RuntimeError(f'yt-dlp failed for {target}: {err.splitlines()[-1] if err else "no output"}')


def channel_tab_url(arg):
    """@handle, handle URL, /channel/UC… URL or bare UC… id → the long-form videos tab."""
    a = arg.strip().rstrip('/')
    if re.fullmatch(r'UC[\w-]{22}', a):
        return f'https://www.youtube.com/channel/{a}/videos'
    if a.startswith('@'):
        return f'https://www.youtube.com/{a}/videos'
    if not a.startswith('http'):
        a = 'https://' + a.lstrip('/') if 'youtube.com' in a else f'https://www.youtube.com/@{a}'
    a = re.sub(r'/(featured|videos|shorts|streams|playlists|community|about|posts)$', '', a)
    return a + '/videos'


def entry_record(e):
    return {'id': e.get('id'), 'title': (e.get('title') or '').strip(), 'views': e.get('view_count'),
            'ts': e.get('timestamp'), 'duration': e.get('duration'), 'channel': e.get('channel') or e.get('uploader'),
            'channel_id': e.get('channel_id'), 'handle': e.get('uploader_id'),
            'short': '/shorts/' in (e.get('url') or ''), 'live': e.get('live_status') in ('is_live', 'is_upcoming')}


# ---------------------------------------------------------------- cache

def load_cache():
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {'channels': {}, 'aliases': {}}


def save_cache(cache):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1))


def cache_ok(entry, limit, max_age_days):
    if not entry:
        return False
    age = (TODAY - dt.date.fromisoformat(entry['fetched'])).days
    complete = len(entry['videos']) < entry['limit'] or entry['limit'] >= limit
    return age <= max_age_days and complete


def channel_listing(cache, url_or_id, limit, max_age_days, refresh, alias=None):
    """A cached-or-fresh channel entry: name, handle, subs, videos (latest `limit` long-form uploads, newest first)."""
    key = cache['aliases'].get((alias or url_or_id).lower(), url_or_id)
    entry = cache['channels'].get(key)
    if not refresh and cache_ok(entry, limit, max_age_days):
        entry = dict(entry, from_cache=True)
        entry['complete'] = len(entry['videos']) < entry['limit']
        entry['videos'] = entry['videos'][:limit]
        return entry
    url = url_or_id if url_or_id.startswith('http') else f'https://www.youtube.com/channel/{url_or_id}/videos'
    data = ytdlp_flat(url, limit)
    vids = [entry_record(e) for e in data.get('entries') or []]
    cid = data.get('channel_id') or key
    entry = {'fetched': TODAY.isoformat(), 'limit': limit, 'url': url, 'channel_id': cid,
             'name': data.get('channel') or data.get('uploader') or cid, 'handle': data.get('uploader_id'),
             'subs': data.get('channel_follower_count'),
             'videos': [{k: v[k] for k in ('id', 'title', 'views', 'ts', 'duration', 'live')} for v in vids]}
    cache['channels'][cid] = entry
    for a in {alias, url_or_id, entry['handle'], cid}:
        if a:
            cache['aliases'][a.lower()] = cid
    save_cache(cache)
    return dict(entry, from_cache=False, complete=len(vids) < limit)


def scored(entry):
    vids = [v for v in entry['videos'] if v['views'] is not None and not v.get('live')]
    med = statistics.median(v['views'] for v in vids) if vids else 0
    return vids, med


# ---------------------------------------------------------------- formatting

def compact(n):
    if n is None:
        return '?'
    for div, suf in ((1e9, 'B'), (1e6, 'M'), (1e3, 'K')):
        if n >= div:
            x = n / div
            return f'{x:.1f}{suf}'.replace('.0' + suf, suf) if x < 100 else f'{x:.0f}{suf}'
    return str(int(n))


def score_s(s):
    return '?' if s is None else f'{s:.1f}x' if s < 100 else f'{s:.0f}x'


def age_days(ts):
    return None if not ts else (time.time() - ts) / 86400


def is_new(ts):
    return (age_days(ts) or 1e9) < NEW_DAYS


def age_s(ts):
    d = age_days(ts)
    if d is None:
        return '?'
    s = ('<1 d' if d < 1 else f'{d:.0f} d' if d < 14 else f'{d / 7:.0f} wk' if d < 60 else f'{d / 30.4:.0f} mo'
         if d < 365 else f'{d / 365.25:.1f} y')
    return f'**{s} (new)**' if d < NEW_DAYS else s


def cell(t):
    return str(t).replace('|', '\\|').replace('\n', ' ')


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(cell(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def link(vid):
    return f'https://youtu.be/{vid}'


def notes(any_new=False, any_tiny=False, extra=(), score_note=True):
    out = ['Notes:', '- Views are YouTube\'s rounded display counts; ages are approximate (from "2 weeks ago"-style text).']
    if any_new:
        out.append(f'- **(new)** = under {NEW_DAYS} days old: still gaining views, so its views and score understate it.')
    if any_tiny:
        out.append(f'- **Tiny median** (under {TINY_MEDIAN:,} views): on channels this small, scores mostly reflect '
                   'promotion (ads, shares, embeds), not the idea.')
    out += [f'- {x}' for x in extra]
    if score_note:
        out.append('- A score is evidence that a concept worked once, not a prediction '
                   '(the same concept reused on one channel can score far apart).')
    return '\n'.join(out)


# ---------------------------------------------------------------- modes

def mode_channels(args, cache, h):
    window = args.latest or (POPULAR_DEFAULT if args.popular else LATEST_DEFAULT)
    parts, pool, any_new, any_tiny = [], [], False, False
    for i, ch in enumerate(args.channels, 1):
        url = channel_tab_url(ch)
        if i > 1:
            time.sleep(random.uniform(*LOOKUP_SLEEP))
        log(f'[{i}/{len(args.channels)}] {ch}: ' + (f'all uploads (up to {window}), sorted by views' if args.popular
                                                    else f'latest {window} uploads') + f' from {url}')
        try:
            e = channel_listing(cache, url, window, 0, args.refresh, alias=ch)
        except RuntimeError as err:
            log(f'  {err}')
            parts.append(f'{h(2)} {ch}\n\nCould not list this channel: {err}')
            continue
        vids, med = scored(e)
        log(f'  {len(vids)} videos, median {compact(med)}' + (' (cached today)' if e['from_cache'] else ''))
        tiny = med < TINY_MEDIAN
        any_tiny |= tiny
        for v in vids:
            v['score'] = v['views'] / med if med else None
            v['chan'], v['subs'] = e['name'], e.get('subs')
        pool += vids
        young = sum(1 for v in vids if is_new(v['ts']))
        subs = f' · {compact(e["subs"])} subscribers' if e.get('subs') else ''
        if args.popular:
            span = ('**Window: all-time**, ' + (f'all {len(vids)} uploads' if e['complete'] else
                                                  f'capped at the latest {len(vids)} uploads (`--latest`)')
                    + ', sorted by views (`--popular`)')
        elif e['complete']:
            span = f'**Window: all {len(vids)} uploads** (the whole tab)'
        else:
            span = f'**Window: the latest {len(vids)} uploads** (`--latest {window}`; `--popular` for all-time)'
        lines = [f'{h(2)} {e["name"]}' + (f' ({e["handle"]})' if e.get('handle') else '') + subs, '',
                 f'{span}. Long-form uploads tab (`/videos`): **Shorts and live streams are excluded.** '
                 f'Fetched {e["fetched"]}. **Median {compact(med)} views**' + (' — **tiny median**' if tiny else '')
                 + ' over this window. Score = views ÷ median.']
        if young:
            lines.append(f'{young} of these uploads {"is" if young == 1 else "are"} under {NEW_DAYS} days old; '
                         'they pull the median down a little.')
        top = sorted(vids, key=lambda v: v['views'], reverse=True)[:15]
        any_new |= any(is_new(v['ts']) for v in top)
        lines += ['', 'Top 15 by score (within one channel this is also the order by views):', '',
                  table(['#', 'Title', 'Views', 'Score', 'Age', 'URL'],
                        [(n, v['title'], compact(v['views']), score_s(v['score']), age_s(v['ts']), link(v['id']))
                         for n, v in enumerate(top, 1)])]
        parts.append('\n'.join(lines))
    if len(args.channels) > 1 and pool:
        for label, key in (('views', 'views'), ('score', 'score')):
            top = sorted(pool, key=lambda v: v[key] or 0, reverse=True)[:15]
            parts.append(f'{h(2)} All channels: top 15 by {label}\n\n' + table(
                ['#', 'Title', 'Channel', 'Subs', 'Views', 'Score', 'Age', 'URL'],
                [(n, v['title'], v['chan'], compact(v['subs']), compact(v['views']), score_s(v['score']),
                  age_s(v['ts']), link(v['id'])) for n, v in enumerate(top, 1)]))
    parts.append(notes(any_new, any_tiny))
    return parts


def search_entries(query, n):
    data = ytdlp_flat(f'ytsearch{n}:{query}')
    return [entry_record(e) for e in data.get('entries') or [] if e.get('id')]


def mode_search(args, cache, h):
    found, shorts, low = {}, 0, 0
    for i, phrase in enumerate(args.phrases, 1):
        if i > 1:
            time.sleep(random.uniform(*LOOKUP_SLEEP))
        log(f'[search {i}/{len(args.phrases)}] ytsearch{args.n}: {phrase}')
        try:
            results = search_entries(phrase, args.n)
        except RuntimeError as err:
            log(f'  {err}')
            continue
        for v in results:
            if v['short']:
                shorts += 1
                continue
            if (v['views'] or 0) < args.min_views:
                low += 1
                continue
            found.setdefault(v['id'], dict(v, phrases=[]))['phrases'].append(phrase)
    # Look up the most-viewed results' channels first, so the --max-channels cap drops the least promising.
    order, seen = [], set()
    for v in sorted(found.values(), key=lambda v: v['views'] or 0, reverse=True):
        if v['channel_id'] and v['channel_id'] not in seen:
            seen.add(v['channel_id'])
            order.append(v['channel_id'])
    chans, fetched, cached_n = {}, 0, 0
    for cid in order:
        cached = cache['channels'].get(cid)
        if not args.refresh and cache_ok(cached, args.median_of, args.cache_days):
            cached_n += 1
            chans[cid] = (scored(dict(cached, videos=cached['videos'][:args.median_of]))[1], cached.get('subs'))
            continue
        if fetched >= args.max_channels:
            continue
        if fetched:
            time.sleep(random.uniform(*LOOKUP_SLEEP))
        fetched += 1
        log(f'  channel {fetched}/{min(len(order) - cached_n, args.max_channels)}: {cid}')
        try:
            e = channel_listing(cache, cid, args.median_of, args.cache_days, args.refresh)
            chans[cid] = (scored(e)[1], e.get('subs'))
        except RuntimeError as err:
            log(f'  {err}')
    rows, unscored, dropped, any_tiny, any_new = [], [], 0, False, False
    for v in found.values():
        if v['channel_id'] not in chans:
            unscored.append(v)
            continue
        med, subs = chans[v['channel_id']]
        if med < args.min_median:
            dropped += 1
            continue
        v['median'], v['subs'], v['score'] = med, subs, (v['views'] / med if med else None)
        rows.append(v)
    rows.sort(key=lambda v: v['score'] or 0, reverse=True)
    multi = len(args.phrases) > 1
    head = (['#', 'Score', 'Views', 'Channel median', 'Subs', 'Title', 'Channel', 'Age'] + (['Phrase'] if multi else [])
            + ['URL'])
    body = []
    for n, v in enumerate(rows, 1):
        tiny = v['median'] < TINY_MEDIAN
        any_tiny |= tiny
        any_new |= is_new(v['ts'])
        body.append([n, score_s(v['score']), compact(v['views']), compact(v['median']) + (' (tiny)' if tiny else ''),
                     compact(v['subs']), v['title'], v['channel'] or '?', age_s(v['ts'])]
                    + (['; '.join(v['phrases'])] if multi else []) + [link(v['id'])])
    lead = (f'Phrases: {"; ".join(chr(34) + p + chr(34) for p in args.phrases)} · top {args.n} YouTube results each · '
            f'channel median over its latest {args.median_of} long-form uploads · score = views ÷ channel median · '
            f'{fetched} channel lookups this run, {cached_n} from the cache.')
    parts = [lead + '\n\n' + (table(head, body) if body else '_No results passed the filters._')]
    extra = []
    if shorts:
        extra.append(f'{shorts} Short{"s" * (shorts != 1)} skipped: their views don\'t compare with a long-form median.')
    if low:
        extra.append(f'{low} result{"s" * (low != 1)} under --min-views {args.min_views:,} skipped.')
    if dropped:
        extra.append(f'{dropped} result{"s" * (dropped != 1)} from channels under --min-median {args.min_median:,} '
                     'dropped.')
    if unscored:
        extra.append(f'{len(unscored)} result{"s" * (len(unscored) != 1)} unscored (beyond --max-channels '
                     f'{args.max_channels}, or the lookup failed): '
                     + '; '.join(f'{v["title"]} ({compact(v["views"])}, {v["channel"]})' for v in unscored[:8])
                     + (' …' if len(unscored) > 8 else ''))
    parts.append(notes(any_new, any_tiny, extra))
    return parts


STOP = set('a an the and or of to in on for with without your you my i is are be it this that how what why when '
           'from by at as vs into can do does get got so just'.split())


def stem(w):
    for suf in ('ing', 'ed', 'es', 's'):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def keywords(t):
    return {stem(w) for w in re.findall(r"[a-z0-9]+(?:'[a-z]+)?", t.lower()) if w not in STOP}


def mode_exists(args, cache, h):
    parts = []
    for i, title in enumerate(args.titles, 1):
        if i > 1:
            time.sleep(random.uniform(*LOOKUP_SLEEP))
        log(f'[exists {i}/{len(args.titles)}] ytsearch{args.n}: {title}')
        try:
            res = search_entries(title, args.n)
        except RuntimeError as err:
            parts.append(f'{h(2)} "{title}"\n\nSearch failed: {err}')
            continue
        q = keywords(title)
        rows, close = [], []
        for n, v in enumerate(res, 1):
            m = len(q & keywords(v['title'])) / len(q) if q else 0
            if m >= 0.6:
                close.append(v)
            rows.append([n, compact(v['views']), v['title'] + (' (Short)' if v['short'] else ''), v['channel'] or '?',
                         age_s(v['ts']), f'{m:.0%}', link(v['id'])])
        if close:
            big = max(close, key=lambda v: v['views'] or 0)
            summary = (f'**{len(close)} of {len(res)} results share ≥ 60 % of the key words.** The most viewed: '
                       f'"{big["title"]}" ({compact(big["views"])} views, {big["channel"]}).')
        else:
            summary = f'No result shares ≥ 60 % of the key words ({", ".join(sorted(q))}).'
        parts.append(f'{h(2)} "{title}"\n\n{summary}\n\n' + table(
            ['#', 'Views', 'Title', 'Channel', 'Age', 'Match', 'URL'], rows))
    parts.append(notes(extra=['Match = share of the searched title\'s key words that appear in the result\'s title. '
                              'It\'s a crude proxy: read the titles, and open the close ones.'], score_note=False))
    return parts


# ---------------------------------------------------------------- output

def new_file(path):
    """--out never changes an existing file: FILE.md, else FILE-2.md, FILE-3.md…"""
    p = Path(path)
    if p.suffix.lower() != '.md':
        p = p.with_name(p.name + '.md')
    p.parent.mkdir(parents=True, exist_ok=True)
    base, k = p.stem, 2
    while p.exists():
        p = p.with_name(f'{base}-{k}.md')
        k += 1
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='mode', required=True)
    c = sub.add_parser('channels', help='median and top outliers per channel')
    c.add_argument('channels', nargs='+', metavar='URL_OR_@HANDLE')
    c.add_argument('--latest', '--limit', type=int, metavar='N',
                   help=f'window: the latest N uploads (default {LATEST_DEFAULT}; with --popular, a cap, '
                        f'default {POPULAR_DEFAULT})')
    c.add_argument('--popular', action='store_true', help='all-time view: every upload, sorted by views')
    s = sub.add_parser('search', help='desire-phrase search ranked by outlier score')
    s.add_argument('phrases', nargs='+', metavar='PHRASE')
    s.add_argument('--n', type=int, default=20, help='results per phrase (default 20)')
    s.add_argument('--min-views', type=int, default=0)
    s.add_argument('--min-median', type=int, default=0, help='drop channels whose median is below this')
    s.add_argument('--max-channels', '--max-lookups', type=int, default=15,
                   help='fresh channel-median lookups per run, most-viewed results first (default 15)')
    s.add_argument('--median-of', type=int, default=30, help='latest N uploads per channel median (default 30)')
    s.add_argument('--cache-days', type=int, default=14, help='reuse cached channel medians up to this old (default 14)')
    e = sub.add_parser('exists', help='originality search for a title and its variations')
    e.add_argument('titles', nargs='+', metavar='TITLE')
    e.add_argument('--n', type=int, default=10, help='results per title (default 10)')
    for p in (c, s, e):
        p.add_argument('--out', metavar='FILE.md', help='write a new markdown file instead of printing')
        p.add_argument('--refresh', action='store_true', help='ignore cached channel listings')
    args = ap.parse_args()

    cache = load_cache()
    subject = {'channels': 'channels', 'search': 'phrases', 'exists': 'titles'}[args.mode]
    what = ', '.join(f'"{x}"' if ' ' in x else x for x in getattr(args, subject))
    # Headings are built with placeholder marks (\x00 per level) and levelled for stdout or a new file.
    h0 = lambda k: '\x00' * k
    body = {'channels': mode_channels, 'search': mode_search, 'exists': mode_exists}[args.mode](args, cache, h0)
    title_line = {'channels': 'Outliers by channel' + (', all-time' if getattr(args, 'popular', False) else ''),
                  'search': 'Desire-phrase search',
                  'exists': 'Originality search'}[args.mode]
    command = 'outliers.py ' + ' '.join(shlex.quote(a) for a in sys.argv[1:])

    def render(base):
        text = f'\x00 {TODAY.isoformat()} · {title_line}: {what}\n\n`{command}`\n\n' + '\n\n'.join(body)
        return re.sub('\x00+', lambda m: '#' * min(base + len(m.group(0)) - 1, 6), text)

    if args.out:
        p = new_file(args.out)
        p.write_text(render(1) + '\n')
        log(f'Wrote {p}' + ('' if str(p) == args.out else f' (not {args.out}: that file exists or lacked .md)'))
    else:
        print(render(2))
    log(f'yt-dlp calls this run: {CALLS}')


if __name__ == '__main__':
    main()
