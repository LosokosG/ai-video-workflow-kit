import json
import os
import subprocess
import sys
import time

import pytest

from conftest import TOOLS, copy_tool, load_module, skip_windows

HOOK = TOOLS / 'hyperframes-lint' / 'hf_lint_hook.py'


@pytest.fixture
def hf(tmp_path, monkeypatch):
    mod = load_module(HOOK, 'hf_lint_hook_under_test')
    monkeypatch.setattr(mod, 'WORKSPACE', tmp_path / 'ws')
    monkeypatch.setattr(mod, 'STATE', tmp_path / 'state')
    return mod


def make_project(root, marker='hyperframes.json'):
    (root / 'compositions').mkdir(parents=True)
    (root / 'index.html').write_text('<html></html>')
    (root / 'compositions' / 'scene.html').write_text('<div></div>')
    if marker:
        (root / marker).write_text('{}')
    return root


# ---------------------------------------------------------------- project_root and skip rules

def test_project_root_finds_hyperframes_json(hf, tmp_path):
    proj = make_project(tmp_path / 'ws' / 'Videos' / 'v1' / '10-Project' / 'demo')
    assert hf.project_root(proj / 'compositions' / 'scene.html') == proj.resolve()
    assert hf.project_root(proj / 'index.html') == proj.resolve()


def test_project_root_accepts_index_plus_compositions(hf, tmp_path):
    proj = make_project(tmp_path / 'ws' / 'Videos' / 'v1' / '10-Project' / 'bare', marker=None)
    assert hf.project_root(proj / 'compositions' / 'scene.html') == proj.resolve()


def test_project_root_none_outside_a_project(hf, tmp_path):
    loose = tmp_path / 'ws' / 'Workflow' / 'notes.html'
    loose.parent.mkdir(parents=True)
    loose.write_text('x')
    assert hf.project_root(loose) is None


@pytest.mark.parametrize('part', ['scratch', 'node_modules', 'renders', '12-Archive', 'backup-2026-01-01'])
def test_project_root_skips_probe_and_archive_folders(hf, tmp_path, part):
    proj = make_project(tmp_path / 'ws' / 'Videos' / 'v1' / '11-Work' / part / 'probe')
    assert hf.project_root(proj / 'index.html') is None


# ---------------------------------------------------------------- version pin

def test_version_for_reads_pin_from_package_json(hf, tmp_path):
    proj = make_project(tmp_path / 'ws' / 'p')
    (proj / 'package.json').write_text(json.dumps({'scripts': {'render': 'npx hyperframes@0.8.65 render .'}}))
    assert hf.version_for(proj) == '0.8.65'


def test_version_for_falls_back_to_default(hf, tmp_path, monkeypatch):
    monkeypatch.setattr(hf, 'DEFAULT_VERSION', '9.9.9')
    proj = make_project(tmp_path / 'ws' / 'p')
    assert hf.version_for(proj) == '9.9.9'                      # no package.json
    (proj / 'package.json').write_text('{not json')
    assert hf.version_for(proj) == '9.9.9'                      # unreadable package.json
    (proj / 'package.json').write_text(json.dumps({'scripts': {'dev': 'npx hyperframes@latest dev'}}))
    assert hf.version_for(proj) == '9.9.9'                      # no numeric pin


def _fresh_import(tmp_path, name):
    script = copy_tool('hyperframes-lint/hf_lint_hook.py', tmp_path / 'ws')
    return load_module(script, name)


def test_default_version_from_workspace_pin_file(tmp_path, monkeypatch):
    monkeypatch.delenv('HYPERFRAMES_VERSION', raising=False)
    (tmp_path / 'ws' / 'Workflow').mkdir(parents=True)
    (tmp_path / 'ws' / 'Workflow' / 'hyperframes-pin.txt').write_text('1.2.3\n')
    assert _fresh_import(tmp_path, 'hf_pin_file').DEFAULT_VERSION == '1.2.3'


def test_default_version_env_beats_pin_file(tmp_path, monkeypatch):
    monkeypatch.setenv('HYPERFRAMES_VERSION', '4.5.6')
    (tmp_path / 'ws' / 'Workflow').mkdir(parents=True)
    (tmp_path / 'ws' / 'Workflow' / 'hyperframes-pin.txt').write_text('1.2.3\n')
    assert _fresh_import(tmp_path, 'hf_pin_env').DEFAULT_VERSION == '4.5.6'


def test_default_version_is_latest_without_pins(tmp_path, monkeypatch):
    monkeypatch.delenv('HYPERFRAMES_VERSION', raising=False)
    assert _fresh_import(tmp_path, 'hf_pin_none').DEFAULT_VERSION == 'latest'


# ---------------------------------------------------------------- accept list and blocking rules

def test_accept_file_parsing(hf, tmp_path):
    proj = make_project(tmp_path / 'ws' / 'p')
    (proj / '.hyperframes-lint-accept').write_text(
        '# deliberate warnings\n'
        'overlap-warning title-card   # the title is meant to overlap\n'
        '\n'
        'slow-font *  # every element\n'
        'lonely-token\n'
        '   # only a comment\n')
    assert hf.accepted(proj) == {('overlap-warning', 'title-card'), ('slow-font', '*')}


def test_accept_file_missing_means_nothing_accepted(hf, tmp_path):
    assert hf.accepted(make_project(tmp_path / 'ws' / 'p')) == set()


def _fake_run(stdout='', stderr='', exc=None):
    def run(cmd, **kw):
        if exc:
            raise exc
        return subprocess.CompletedProcess(cmd, 0, stdout, stderr)
    return run


def test_lint_blocks_errors_and_unaccepted_warnings_only(hf, tmp_path, monkeypatch):
    proj = make_project(tmp_path / 'ws' / 'p')
    (proj / '.hyperframes-lint-accept').write_text('w-by-id el1\nw-any *\n')
    findings = [
        {'severity': 'error', 'code': 'e1', 'elementId': 'el1'},       # errors can't be accepted
        {'severity': 'warning', 'code': 'w-by-id', 'elementId': 'el1'},  # accepted by id
        {'severity': 'warning', 'code': 'w-by-id', 'elementId': 'el2'},  # other element: blocks
        {'severity': 'warning', 'code': 'w-any', 'elementId': 'x'},      # accepted by *
        {'severity': 'warning', 'code': 'w-new'},                        # no id, not accepted: blocks
        {'severity': 'info', 'code': 'i1'},                              # never blocks
    ]
    monkeypatch.setattr(hf.subprocess, 'run', _fake_run('npx noise\n' + json.dumps({'findings': findings})))
    block, note = hf.lint(proj)
    assert note == ''
    assert [(f['code'], f.get('elementId')) for f in block] == [('e1', 'el1'), ('w-by-id', 'el2'), ('w-new', None)]


def test_lint_without_json_reports_a_note_and_blocks_nothing(hf, tmp_path, monkeypatch):
    proj = make_project(tmp_path / 'ws' / 'p')
    monkeypatch.setattr(hf.subprocess, 'run', _fake_run('', 'npm ERR! boom'))
    block, note = hf.lint(proj)
    assert block == [] and 'gave no JSON' in note


def test_lint_that_cannot_start_blocks_nothing(hf, tmp_path, monkeypatch):
    proj = make_project(tmp_path / 'ws' / 'p')
    monkeypatch.setattr(hf.subprocess, 'run', _fake_run(exc=FileNotFoundError('npx')))
    block, note = hf.lint(proj)
    assert block == [] and 'could not run' in note


# ---------------------------------------------------------------- the CLI as the hooks call it, with a stub npx

ERROR = {'findings': [{'severity': 'error', 'code': 'missing-id', 'elementId': 'card', 'message': 'needs an id',
                       'fixHint': 'add id="card"'}]}
WARNING = {'findings': [{'severity': 'warning', 'code': 'slow-anim', 'elementId': 'card', 'message': 'slow'}]}
CLEAN = {'findings': []}

NPX = '''import json, os, sys
with open(os.environ['NPX_LOG'], 'a') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
sys.stdout.write(os.environ.get('FAKE_LINT', '{"findings": []}'))
'''


@pytest.fixture
def cli(tmp_path, fakebin):
    ws = tmp_path / 'ws'
    script = copy_tool('hyperframes-lint/hf_lint_hook.py', ws)
    proj = make_project(ws / 'Videos' / 'v1' / '10-Project' / 'demo')
    fakebin('npx', NPX)
    log = tmp_path / 'npx.log'
    (tmp_path / 'tmp').mkdir()

    def run(mode, stdin=None, lint=CLEAN, args=(), raw_stdin=None):
        env = dict(os.environ, PATH=f'{fakebin.dir}{os.pathsep}{os.environ.get("PATH", "")}', NPX_LOG=str(log),
                   FAKE_LINT=lint if isinstance(lint, str) else json.dumps(lint), TMPDIR=str(tmp_path / 'tmp'))
        env.pop('HYPERFRAMES_VERSION', None)
        data = raw_stdin if raw_stdin is not None else (json.dumps(stdin) if stdin is not None else '')
        return subprocess.run([sys.executable, str(script), mode, *args], input=data, capture_output=True,
                              text=True, env=env, cwd=ws, timeout=60)

    def calls():
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    run.ws, run.proj, run.calls = ws, proj, calls
    return run


def edit(path, session='s1'):
    return {'session_id': session, 'tool_name': 'Edit', 'tool_input': {'file_path': str(path)}}


pytestmark = skip_windows


def test_post_error_exits_2_with_report(cli):
    r = cli('post', edit(cli.proj / 'index.html'), ERROR)
    assert r.returncode == 2
    assert 'HyperFrames lint: 1 finding(s) to fix in Videos/v1/10-Project/demo' in r.stderr
    assert 'ERROR missing-id [card]' in r.stderr and 'Fix: add id="card"' in r.stderr
    assert cli.calls() == [['--yes', 'hyperframes@latest', 'lint', '--json', str(cli.proj.resolve())]]


def test_post_uses_project_pin(cli):
    (cli.proj / 'package.json').write_text(json.dumps({'scripts': {'lint': 'npx hyperframes@0.8.65 lint'}}))
    assert cli('post', edit(cli.proj / 'index.html'), CLEAN).returncode == 0
    assert cli.calls()[0][1] == 'hyperframes@0.8.65'


def test_post_clean_exits_0(cli):
    assert cli('post', edit(cli.proj / 'compositions' / 'scene.html'), CLEAN).returncode == 0


def test_post_unaccepted_warning_blocks_accepted_does_not(cli):
    assert cli('post', edit(cli.proj / 'index.html'), WARNING).returncode == 2
    (cli.proj / '.hyperframes-lint-accept').write_text('slow-anim card  # intentional\n')
    assert cli('post', edit(cli.proj / 'index.html'), WARNING).returncode == 0


def test_post_ignores_scratch_projects_and_other_files(cli):
    probe = make_project(cli.ws / 'Videos' / 'v1' / '11-Work' / 'scratch' / 'probe')
    assert cli('post', edit(probe / 'index.html'), ERROR).returncode == 0
    notes = cli.proj / 'NOTES.md'
    notes.write_text('x')
    assert cli('post', edit(notes), ERROR).returncode == 0
    assert cli.calls() == []


def test_post_never_blocks_on_a_broken_lint_run(cli):
    r = cli('post', edit(cli.proj / 'index.html'), 'this is not json')
    assert r.returncode == 0 and 'gave no JSON' in r.stderr


def test_post_with_invalid_hook_json_exits_0(cli):
    assert cli('post', raw_stdin='not json').returncode == 0


@pytest.mark.parametrize('header', ['Update File', 'Add File'])
def test_codex_apply_patch_paths_are_found(cli, header):
    patch = (f'*** Begin Patch\n*** {header}: Videos/v1/10-Project/demo/compositions/scene.html\n'
             '@@\n-<div></div>\n+<div id="x"></div>\n*** End Patch\n')
    hook = {'session_id': 'c1', 'tool_name': 'apply_patch', 'cwd': str(cli.ws), 'tool_input': {'command': patch}}
    assert cli('post', hook, ERROR).returncode == 2
    assert len(cli.calls()) == 1


def test_codex_apply_patch_move_target_and_raw_string_input(cli):
    patch = ('*** Begin Patch\n*** Update File: Workflow/old.txt\n*** Move to: Videos/v1/10-Project/demo/index.html\n'
             '*** End Patch\n')
    hook = {'session_id': 'c2', 'cwd': str(cli.ws), 'tool_input': patch}
    assert cli('post', hook, ERROR).returncode == 2


def test_stop_hook_active_guard_never_loops(cli):
    r = cli('stop', {'session_id': 's1', 'stop_hook_active': True}, ERROR)
    assert r.returncode == 0 and cli.calls() == []


def test_stop_lints_projects_touched_this_session(cli):
    old = time.time() - 3 * 3600                     # outside the 60-minute recent-edit window
    for p in [cli.proj / 'index.html', cli.proj / 'compositions' / 'scene.html']:
        os.utime(p, (old, old))
    assert cli('stop', {'session_id': 's9'}, ERROR).returncode == 0      # nothing touched yet
    assert cli('post', edit(cli.proj / 'index.html', session='s9'), CLEAN).returncode == 0
    r = cli('stop', {'session_id': 's9'}, ERROR)
    assert r.returncode == 2 and 'missing-id' in r.stderr
    assert cli('stop', {'session_id': 'other'}, ERROR).returncode == 0   # another session didn't touch it


def test_stop_lints_recently_modified_projects(cli):
    r = cli('stop', {'session_id': 'fresh'}, ERROR)                       # files were just written
    assert r.returncode == 2


def test_check_mode_exit_codes(cli):
    assert cli('check', lint=ERROR, args=[str(cli.proj)]).returncode == 1
    r = cli('check', lint=CLEAN, args=[str(cli.proj)])
    assert r.returncode == 0 and 'lint clean' in r.stdout
    r = cli('check', lint=ERROR, args=[str(cli.ws / 'Workflow')])
    assert r.returncode == 0 and 'No HyperFrames project found' in r.stdout
