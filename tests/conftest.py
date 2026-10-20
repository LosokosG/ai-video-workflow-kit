import importlib.util
import os
import shutil
import stat
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WS = REPO / 'workspace'
TOOLS = WS / 'Workflow' / 'Tools'


def load_module(path, name):
    """Import a tool script by path (the tools are scripts, not a package)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def copy_tool(rel, ws):
    """Copy a tool into a scratch workspace at the same relative path, so its parents[N] root is the scratch one."""
    dst = ws / 'Workflow' / 'Tools' / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TOOLS / rel, dst)
    return dst


@pytest.fixture
def fakebin(tmp_path):
    """Return make(name, python_body) that writes an executable stub, run by this interpreter, into one bin dir."""
    d = tmp_path / 'fakebin'
    d.mkdir()

    def make(name, body):
        p = d / name
        p.write_text(f'#!{sys.executable}\n{body}')
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return p

    make.dir = d
    return make


skip_windows = pytest.mark.skipif(os.name == 'nt', reason='stub executables need a POSIX shebang')
