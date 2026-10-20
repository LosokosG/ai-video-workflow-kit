#!/usr/bin/env python3
"""Make each skill in .agents/skills/ visible to Claude Code as .claude/skills/<name>, and CLAUDE.md -> AGENTS.md.

Uses relative symlinks; on Windows (or where symlinks aren't allowed) it copies instead and says so.
Safe to re-run after installing more skills (for example `npx skills add heygen-com/hyperframes`).
"""
import os, shutil, sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
skills, links = root / '.agents' / 'skills', root / '.claude' / 'skills'
links.mkdir(parents=True, exist_ok=True)
copied = False


def link(target, dest, is_dir):
    global copied
    if dest.is_symlink() or dest.exists():
        return False
    try:
        os.symlink(os.path.relpath(target, dest.parent), dest, target_is_directory=is_dir)
    except (OSError, NotImplementedError):
        (shutil.copytree if is_dir else shutil.copy2)(target, dest)
        copied = True
    return True


made = [s.name for s in sorted(skills.iterdir()) if s.is_dir() and (s / 'SKILL.md').is_file() and link(s, links / s.name, True)]
if link(root / 'AGENTS.md', root / 'CLAUDE.md', False):
    made.append('CLAUDE.md')
print(f'linked {len(made)}: ' + ', '.join(made) if made else 'nothing to do: every skill is already linked')
if copied:
    print('Symlinks were not possible here, so files were copied. Re-run this script after editing AGENTS.md or a skill.')
