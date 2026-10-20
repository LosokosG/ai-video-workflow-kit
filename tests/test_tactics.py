import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import TOOLS, WS, load_module

TACTICS_DIR = WS / 'Workflow' / 'Tactics'
EXPECTED = {
    'ideas/problem-log', 'titles-thumbnails/show-the-real-result', 'retention/measure-the-hook',
    'retention/keep-useful-explanations', 'retention/audible-music-bed', 'shorts/rebuild-from-layers',
}


@pytest.fixture(scope='module')
def tactics():
    return load_module(TOOLS / 'tactics' / 'tactics.py', 'tactics_under_test')


@pytest.fixture(scope='module')
def cards(tactics):
    return {f"{t['lib']}/{t['slug']}": t for t in tactics.load()}


def test_library_holds_the_example_cards(cards):
    assert set(cards) == EXPECTED


def test_card_parsing(cards):
    hook = cards['retention/measure-the-hook']
    assert hook['name'] == 'Measure the hook before every review render'
    assert hook['stages'] == ['hook'] and hook['status'] == 'candidate'
    assert hook['formats'] == {'long'} and hook['face'] == {'any'} and hook['mode'] == {'any'} and hook['core']
    assert hook['pick'].startswith('Measure the first 30 s')
    assert hook['fields']['Check'].startswith('The review note lists')

    pkg = cards['titles-thumbnails/show-the-real-result']
    assert pkg['role'] == 'credibility' and pkg['stages'] == ['title', 'thumbnail'] and pkg['core']

    short = cards['shorts/rebuild-from-layers']
    assert short['formats'] == {'short'} and short['mode'] == {'cut'} and not short['core']

    assert not cards['retention/audible-music-bed']['core']


def test_parse_rejects_a_card_without_the_header(tactics, tmp_path):
    md = tmp_path / 'retention' / 'broken' / 'TACTIC.md'
    md.parent.mkdir(parents=True)
    md.write_text('# Broken\n\nno header line here\n')
    with pytest.raises(SystemExit, match='line 3 must read'):
        tactics.parse(md)


def found(tactics, cards, **a):
    return {k for k, t in cards.items() if tactics.matches(t, a)}


def test_find_filters(tactics, cards):
    assert found(tactics, cards, format='short') == {'shorts/rebuild-from-layers'}
    assert found(tactics, cards, format='long', stage='hook') == {'retention/measure-the-hook'}
    assert found(tactics, cards, core=True) == {'retention/measure-the-hook', 'retention/keep-useful-explanations',
                                                'titles-thumbnails/show-the-real-result'}
    assert found(tactics, cards, lib='ideas') == {'ideas/problem-log'}
    assert found(tactics, cards, text='music speakers') == {'retention/audible-music-bed'}
    assert found(tactics, cards, text='no-such-words') == set()
    assert found(tactics, cards, format='short', mode='native') == set()          # the only short card is mode: cut
    assert found(tactics, cards, format='short', mode='cut') == {'shorts/rebuild-from-layers'}
    assert len(found(tactics, cards, face='presenter')) == len(cards)              # face defaults to any


def test_args_parser(tactics):
    assert tactics.args(['--format', 'long', '--core', 'a', '--full', 'b']) == {
        'format': 'long', 'core': True, 'slugs': ['a', 'b'], 'full': True}


def run_tool(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, cwd=cwd, timeout=60)


def test_cli_find_and_show():
    r = run_tool(TOOLS / 'tactics' / 'tactics.py', 'find', '--format', 'long', '--stage', 'sound')
    assert r.returncode == 0
    assert r.stdout.startswith('retention/audible-music-bed · Carve the music around speech')
    assert '-- 1 of 6' in r.stderr
    r = run_tool(TOOLS / 'tactics' / 'tactics.py', 'show', 'shorts/rebuild-from-layers', 'nope')
    assert '## Rebuild cut-down shorts from layers  (shorts/rebuild-from-layers; short; candidate)' in r.stdout
    assert 'no tactic nope' in r.stdout


@pytest.fixture
def library_copy(tmp_path):
    """The tactics tools and library copied into a scratch workspace (build_index writes next to the cards)."""
    shutil.copytree(TOOLS / 'tactics', tmp_path / 'Workflow' / 'Tools' / 'tactics',
                    ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(TACTICS_DIR, tmp_path / 'Workflow' / 'Tactics')
    return tmp_path / 'Workflow'


def tree(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file())


def test_index_rebuild_matches_committed_files(library_copy):
    """Golden test: rebuilding from the committed cards reproduces the committed INDEX, SHORTS-INDEX and picks/."""
    shutil.rmtree(library_copy / 'Tactics' / 'picks')
    r = run_tool(library_copy / 'Tools' / 'tactics' / 'build_index.py')
    assert r.returncode == 0, r.stderr
    assert "long  {'Idea': 1, 'Title and thumbnail': 1, 'Hook (intro)': 1, 'Structure and script': 1, 'Sound': 1, 'core': 3}" in r.stdout
    assert tree(library_copy / 'Tactics') == tree(TACTICS_DIR)
    for rel in tree(TACTICS_DIR):
        assert filecmp.cmp(library_copy / 'Tactics' / rel, TACTICS_DIR / rel, shallow=False), rel


def test_index_rebuild_is_idempotent_and_counts_new_cards(library_copy):
    build = library_copy / 'Tools' / 'tactics' / 'build_index.py'
    run_tool(build)
    first = (library_copy / 'Tactics' / 'INDEX.md').read_text()
    run_tool(build)
    assert (library_copy / 'Tactics' / 'INDEX.md').read_text() == first

    card = library_copy / 'Tactics' / 'retention' / 'second-hook-card' / 'TACTIC.md'
    card.parent.mkdir()
    card.write_text('# Second hook card\n\n`retention` · stages: hook · status: used · source: test\n\n'
                    '**Pick:** A second hook card\n\n**What:** x\n\n**Why it works:** x\n\n**How we apply it:** x\n\n'
                    '**Use when / skip when:** x\n\n**Check:** x\n\n## Used in\n\n(date · video · where · result)\n')
    r = run_tool(build)
    assert "'Hook (intro)': 2" in r.stdout
    hook = (library_copy / 'Tactics' / 'picks' / 'long-hook.md').read_text()
    assert '[Second hook card](../retention/second-hook-card/TACTIC.md) **[used]**' in hook
    assert '| Hook (intro) | [`picks/long-hook.md`](picks/long-hook.md) | 2 |' in (library_copy / 'Tactics' / 'INDEX.md').read_text()


def test_tactics_build_command_runs_build_index(library_copy):
    (library_copy / 'Tactics' / 'picks' / 'long-idea.md').unlink()
    r = run_tool(library_copy / 'Tools' / 'tactics' / 'tactics.py', 'build')
    assert r.returncode == 0 and (library_copy / 'Tactics' / 'picks' / 'long-idea.md').is_file()
