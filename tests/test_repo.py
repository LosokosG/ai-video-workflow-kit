"""Repository validator: skills, markdown links, tactic cards and config files are consistent."""
import json
import re
from pathlib import Path

import pytest

from conftest import REPO, TOOLS, WS, load_module

SKILLS = WS / '.agents' / 'skills'
EXPECTED_SKILLS = {
    'video-ideas', 'video-brief', 'video-intro', 'youtube-editing-workflow', 'retention-review', 'video-packaging',
    'video-closeout', 'video-performance', 'video-study', 'video-lessons', 'presenter-finishing', 'short-plan',
    'short-edit', 'short-publish',
}
SKIP_DIRS = {'.git', '.pytest_cache', '__pycache__', '.venv', 'node_modules'}


def repo_files(pattern):
    return sorted(p for p in REPO.rglob(pattern) if not SKIP_DIRS & set(p.relative_to(REPO).parts))


def frontmatter(path):
    text = path.read_text()
    assert text.startswith('---\n'), f'{path}: no front matter'
    block = text[4:text.index('\n---\n', 4)]
    out = {}
    for line in block.splitlines():
        key, sep, value = line.partition(':')
        assert sep, f'{path}: bad front-matter line {line!r}'
        out[key.strip()] = value.strip()
    return out


def test_skill_set():
    assert {p.name for p in SKILLS.iterdir() if p.is_dir()} == EXPECTED_SKILLS


@pytest.mark.parametrize('skill', sorted(EXPECTED_SKILLS))
def test_skill_front_matter(skill):
    fm = frontmatter(SKILLS / skill / 'SKILL.md')
    assert fm.get('name') == skill
    assert 0 < len(fm.get('description', '')) < 1024
    assert fm['description'].startswith('Use when')


LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
FENCE = re.compile(r'^```.*?^```', re.S | re.M)


def relative_links():
    for md in repo_files('*.md'):
        text = FENCE.sub('', md.read_text())
        for target in LINK.findall(text):
            if re.match(r'^[a-z][a-z0-9+.-]*:', target) or target.startswith('#'):
                continue
            yield md, target


def test_there_are_relative_links_to_check():
    assert len(list(relative_links())) > 20


def test_every_relative_markdown_link_resolves():
    broken = [f'{md.relative_to(REPO)} -> {t}' for md, t in relative_links()
              if not (md.parent / t.split('#', 1)[0]).exists()]
    assert broken == []


HEADER = re.compile(r'^`(?P<lib>[a-z-]+)` · (?:(?:formats|role|face|mode|core): [a-z, -]+ · )*'
                    r'stages: [a-z, -]+ · status: (?P<status>[^·]+?) · source: \S.*$')
FIELDS = ['**What:**', '**Why it works:**', '**How we apply it:**', '**Use when / skip when:**', '**Check:**']
STATUS = re.compile(r'^(candidate|used|proven|dropped \(.+\)|skip by default \(.+\))$')
CARDS = sorted((WS / 'Workflow' / 'Tactics').glob('*/*/TACTIC.md'))


def test_cards_exist():
    assert len(CARDS) == 6


@pytest.mark.parametrize('card', CARDS, ids=lambda p: f'{p.parent.parent.name}/{p.parent.name}')
def test_tactic_card_schema(card):
    lines = card.read_text().splitlines()
    assert lines[0].startswith('# ') and lines[1] == ''
    m = HEADER.match(lines[2])
    assert m, f'header line: {lines[2]!r}'
    assert m['lib'] == card.parent.parent.name
    assert STATUS.match(m['status'])
    assert re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', card.parent.name)
    pick = next(l for l in lines if l.startswith('**Pick:** '))
    assert len(pick) - len('**Pick:** ') <= 90
    text = '\n'.join(lines)
    positions = [text.index(f) for f in FIELDS]
    assert positions == sorted(positions), 'fields out of order'
    assert '**Source:** ' in text and '\n## Used in\n' in text
    assert 'youtube.com' not in text and 'youtu.be' not in text


def test_cards_parse_with_the_tactics_tool():
    tactics = load_module(TOOLS / 'tactics' / 'tactics.py', 'tactics_for_validator')
    assert len(tactics.load()) == len(CARDS)


def test_setup_guide_copy_is_identical():
    assert (REPO / 'SETUP-FOR-AGENT.md').read_text() == (WS / 'docs' / 'SETUP.md').read_text()


REMOVED = ['Pipelines/Shorts', 'Pipelines/Presenter', 'Pipelines/Business', 'talking-head-recut', 'claims-register',
           'brand-deals', 'starting-points', 'Tactics/personal', 'SHORTS-PLAYBOOK']


def test_no_references_to_material_that_is_not_shipped():
    hits = []
    for p in repo_files('*'):
        if not p.is_file() or p.parent.name == 'tests' or p.suffix not in {'.md', '.py', '.json', '.toml', '.yml'}:
            continue
        text = p.read_text()
        hits += [f'{p.relative_to(REPO)}: {r}' for r in REMOVED if r in text]
    assert hits == []


def test_hook_configs_point_at_the_lint_hook():
    hook = 'Workflow/Tools/hyperframes-lint/hf_lint_hook.py'
    assert (WS / hook).is_file()
    claude = json.loads((WS / '.claude' / 'settings.json').read_text())
    commands = [h['command'] for event in claude['hooks'].values() for group in event for h in group['hooks']]
    assert sorted(c.rsplit(' ', 1)[1] for c in commands) == ['post', 'stop']
    assert all(hook in c for c in commands)


def test_codex_config_mirrors_the_hooks():
    tomllib = pytest.importorskip('tomllib')
    cfg = tomllib.loads((WS / '.codex' / 'config.toml').read_text())
    commands = {event: [h['command'] for group in cfg['hooks'][event] for h in group['hooks']]
                for event in ('PostToolUse', 'Stop')}
    assert commands == {'PostToolUse': ['python3 Workflow/Tools/hyperframes-lint/hf_lint_hook.py post'],
                        'Stop': ['python3 Workflow/Tools/hyperframes-lint/hf_lint_hook.py stop']}


def test_python_tools_have_no_third_party_imports_except_feedcheck():
    allowed = {'PIL': 'feedcheck.py', 'faster_whisper': 'study.py'}   # study.py runs whisper in a child interpreter
    for py in sorted(TOOLS.rglob('*.py')):
        for m in re.finditer(r'^(?:from|import) ([A-Za-z_][\w.]*)', py.read_text(), re.M):
            top = m.group(1).split('.')[0]
            if top in allowed:
                assert py.name == allowed[top], py
                continue
            if top == 'tactics':
                continue                                   # build_index imports its sibling
            assert top in __import__('sys').stdlib_module_names, f'{py.name}: {top}'
