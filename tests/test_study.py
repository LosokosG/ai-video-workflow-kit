import json

import pytest

from conftest import TOOLS, load_module


@pytest.fixture(scope='module')
def s():
    # stdlib-only import: no ffmpeg, yt-dlp or faster-whisper is needed until a command runs
    return load_module(TOOLS / 'study' / 'study.py', 'study_under_test')


@pytest.mark.parametrize('text, value', [('42', 42.0), ('1:02.5', 62.5), ('00:01,250', 1.25), ('1:00:00', 3600.0),
                                         (' 2:03 ', 123.0), (7, 7.0)])
def test_secs_parses_timestamps(s, text, value):
    assert s.secs(text) == pytest.approx(value)


def test_stamp_formats(s):
    assert s.stamp(62.5, tenths=True) == '01:02.5'
    assert s.stamp(59.9) == '00:59'
    assert s.stamp(3661) == '1:01:01'


def test_merge_close_keeps_one_detection_per_burst(s):
    assert s.merge_close([0.0, 0.1, 0.25, 1.0, 1.15, 1.3, 2.0]) == [0.0, 1.0, 2.0]
    assert s.merge_close([0.0, 0.5, 1.0]) == [0.0, 0.5, 1.0]
    assert s.merge_close([0.0, 0.5], gap=0.6) == [0.0]
    assert s.merge_close([]) == []


def test_still_stretches(s):
    diffs = [0.0] * 16 + [5.0] + [0.1] * 4 + [3.0] + [0.2] * 13
    # 16 calm steps of 0.25 s = 4.0 s from 0.0; 4 steps = 1 s (too short); 13 steps = 3.25 s from 5.5 s
    assert s.still_stretches(diffs, 0.25) == [(4.0, 0.0), (3.25, 5.5)]
    assert s.still_stretches([1.0] * 20, 0.25) == []


def test_block_diffs_and_motion_series(s):
    w, h = 64, 36
    black, grey = bytes(w * h), bytes([2]) * (w * h)
    d = s.block_diffs(black, grey)
    assert len(d) == (h // 6) * (w // 8) and set(d) == {2.0}
    act, means = s.motion_series([black, black, grey])
    assert means == [0.0, 2.0] and len(act) == 2


def test_clip_time_maps_to_source_time_through_the_sidecar(s, tmp_path):
    clip = tmp_path / 'clip.mp4'
    clip.write_bytes(b'')
    assert s.offset_of(clip) == 0.0                                   # no sidecar: a whole file
    (tmp_path / 'clip.mp4.json').write_text(json.dumps({'source_start_s': 75.5, 'url': 'https://example.com/v'}))
    assert s.offset_of(clip) == 75.5
    assert s.sidecar(clip)['url'] == 'https://example.com/v'


def test_span_args_builds_input_seeking(s):
    assert s.span_args('in.mp4', {'--start': '1:00', '--end': '90'}, dur=120) == (
        60.0, 90.0, ['-ss', '60.000', '-to', '90.000', '-i', 'in.mp4'])
    assert s.span_args('in.mp4', {'--end': '500'}, dur=120) == (0.0, 120, ['-i', 'in.mp4'])
    with pytest.raises(SystemExit, match='empty range'):
        s.span_args('in.mp4', {'--start': '100', '--end': '50'}, dur=120)


def test_cli_parse(s):
    assert s.parse(['a.mp4', '--start', '5', '--words', 'out.txt'], ('--start',)) == (
        ['a.mp4', 'out.txt'], {'--start': '5', '--words': True})


def test_vtt_rolling_captions_are_deduplicated(s, tmp_path):
    vtt = tmp_path / 'c.vtt'
    vtt.write_text(
        'WEBVTT\n\n'
        '00:00:01.000 --> 00:00:03.000\nhello <c>there</c>\n \n\n'
        '00:00:03.000 --> 00:00:03.010\nhello there\n\n'               # 10 ms hold cue: skipped
        '00:00:03.010 --> 00:00:05.000\nhello there\nthis is &amp; that\n\n'
        '00:00:05.000 --> 00:00:07.000\nthis is &amp; that\nnew line\n')
    assert s.vtt_to_lines(vtt) == [(1.0, 'hello there'), (3.01, 'this is & that'), (5.0, 'new line')]


def test_caption_choice_order(s):
    info = {'language': 'pl', 'subtitles': {'pl': [], 'live_chat': []},
            'automatic_captions': {'pl-orig': [], 'pl': [], 'en': []}}
    choices = s.caption_choices(info)
    assert choices[0] == ('pl', 'manual')
    assert choices[1] == ('pl-orig', 'auto (original-language speech recognition)')
    assert choices[-1][0] == 'en' and 'TRANSLATED' in choices[-1][1]


def test_with_t_adds_youtube_timestamps_only(s):
    assert s.with_t('https://www.youtube.com/watch?v=x', 75.9) == 'https://www.youtube.com/watch?v=x&t=75s'
    assert s.with_t('https://youtu.be/x', 5) == 'https://youtu.be/x?t=5s'
    assert s.with_t('/local/file.mp4', 5) == '/local/file.mp4'
