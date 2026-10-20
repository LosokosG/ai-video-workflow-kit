import argparse
import datetime as dt
import time

import pytest

from conftest import TOOLS, load_module


@pytest.fixture
def o(tmp_path, monkeypatch):
    mod = load_module(TOOLS / 'ideas' / 'outliers.py', 'outliers_under_test')
    monkeypatch.setattr(mod, 'CACHE', tmp_path / 'cache' / 'channels.json')
    monkeypatch.setattr(mod.time, 'sleep', lambda s: None)
    return mod


@pytest.mark.parametrize('arg, url', [
    ('@SomeChannel', 'https://www.youtube.com/@SomeChannel/videos'),
    ('SomeChannel', 'https://www.youtube.com/@SomeChannel/videos'),
    ('UC' + 'a' * 22, 'https://www.youtube.com/channel/UC' + 'a' * 22 + '/videos'),
    ('https://www.youtube.com/@SomeChannel/featured', 'https://www.youtube.com/@SomeChannel/videos'),
    ('https://www.youtube.com/@SomeChannel/shorts/', 'https://www.youtube.com/@SomeChannel/videos'),
    ('youtube.com/@SomeChannel', 'https://youtube.com/@SomeChannel/videos'),
    ('https://www.youtube.com/channel/UC' + 'b' * 22, 'https://www.youtube.com/channel/UC' + 'b' * 22 + '/videos'),
])
def test_handle_to_videos_tab_url(o, arg, url):
    assert o.channel_tab_url(arg) == url


def test_median_ignores_missing_views_and_live_streams(o):
    entry = {'videos': [{'views': 100}, {'views': 300}, {'views': None}, {'views': 200},
                        {'views': 10_000, 'live': True}]}
    vids, med = o.scored(entry)
    assert [v['views'] for v in vids] == [100, 300, 200] and med == 200


def test_median_of_even_count_and_empty_channel(o):
    assert o.scored({'videos': [{'views': 100}, {'views': 400}]})[1] == 250
    assert o.scored({'videos': []}) == ([], 0)


@pytest.mark.parametrize('n, s', [(None, '?'), (999, '999'), (1000, '1K'), (1500, '1.5K'), (163_000, '163K'),
                                  (5_800_000, '5.8M'), (2_000_000_000, '2B')])
def test_compact_counts(o, n, s):
    assert o.compact(n) == s


@pytest.mark.parametrize('score, s', [(None, '?'), (3.0, '3.0x'), (35.6, '35.6x'), (150, '150x')])
def test_score_format(o, score, s):
    assert o.score_s(score) == s


def test_keywords_drop_stopwords_and_stem(o):
    assert o.keywords('How I use Claude Code to edit videos') == {'use', 'claude', 'code', 'edit', 'video'}
    assert o.stem('testing') == 'test' and o.stem('is') == 'is'


def test_cache_freshness(o):
    today = o.TODAY.isoformat()
    old = (o.TODAY - dt.timedelta(days=20)).isoformat()
    full = {'fetched': today, 'limit': 60, 'videos': [{}] * 60}       # listing hit its limit: may have more uploads
    short = {'fetched': today, 'limit': 60, 'videos': [{}] * 12}      # the whole channel
    assert o.cache_ok(full, 60, 0) and not o.cache_ok(full, 100, 0)
    assert o.cache_ok(short, 100, 0)
    assert not o.cache_ok(dict(short, fetched=old), 60, 14)
    assert not o.cache_ok(None, 60, 14)


def test_new_file_never_overwrites(o, tmp_path):
    (tmp_path / 'r.md').write_text('old')
    (tmp_path / 'r-2.md').write_text('old')
    assert o.new_file(tmp_path / 'r.md') == tmp_path / 'r-3.md'
    assert o.new_file(tmp_path / 'sub' / 'notes') == tmp_path / 'sub' / 'notes.md'
    assert (tmp_path / 'sub').is_dir()


def test_video_link(o):
    assert o.link('abc123') == 'https://youtu.be/abc123'


def test_channels_mode_scores_against_the_channel_median(o, monkeypatch):
    now = time.time()
    listing = {'channel_id': 'UC' + 'c' * 22, 'channel': 'Example', 'uploader_id': '@example',
               'channel_follower_count': 12_000,
               'entries': [{'id': f'v{i}', 'title': f'Video {i}', 'view_count': v, 'timestamp': now - 90 * 86400}
                           for i, v in enumerate([1000, 2000, 3000, 30_000, 500])]}
    calls = []
    monkeypatch.setattr(o, 'ytdlp_flat', lambda target, end=None: calls.append((target, end)) or listing)
    args = argparse.Namespace(channels=['@example'], latest=None, popular=False, refresh=True)
    parts = o.mode_channels(args, o.load_cache(), lambda k: '#' * k)
    text = '\n'.join(parts)
    assert calls == [('https://www.youtube.com/@example/videos', o.LATEST_DEFAULT)]
    assert '**Median 2K views**' in text and '12K subscribers' in text
    assert '| 1 | Video 3 | 30K | 15.0x |' in text                   # 30 000 / 2 000
    assert '| 5 | Video 4 | 500 | 0.2x |' in text
    assert 'https://youtu.be/v3' in text
    assert o.CACHE.is_file()                                          # listing cached for the next run
