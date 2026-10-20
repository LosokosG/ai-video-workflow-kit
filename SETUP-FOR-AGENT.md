# Setup guide for the AI agent (read this fully, then do it)

You are an AI coding agent (Claude Code, Codex, or any agent that can read files and run shell commands). Your user has been given a **video-workflow starter kit**: a ready-made workspace of instructions, skills, templates and small tools for planning, editing and publishing YouTube videos (long-form and Shorts/TikTok/Reels) with an AI agent. Your job now is to **set it up on this user's machine, install what it needs, and adapt it to their setup**. Then the user works with you in that workspace day to day.

The kit came from one creator's private workspace, cleaned of their videos and personal material. Some defaults reflect that creator's taste and hardware; the user should be able to change any of them. The kit needs no account and sends none of the user's files anywhere. Network use: installing tools and the HyperFrames skills, the HyperFrames lint hook (`npx` fetches the HyperFrames CLI; pin a version in `Workflow/hyperframes-pin.txt` to avoid "latest"), and the research tools reading public YouTube data through `yt-dlp` (no login).

## How to behave

- Do the technical work yourself. Ask the user only for choices that change the result (listed in step 1) or for things only they can provide.
- Ask before running anything with `sudo`, installing system packages, or installing a global tool. Say what it is and why. Project-local installs (a venv in the workspace, `npx`) don't need a question.
- Never delete files. If something must go, move it to the OS trash (`gio trash` on Linux, `trash` or Finder on macOS, the Recycle Bin on Windows) and tell the user.
- Never overwrite files the user already has. If the target folder exists and isn't empty, stop and ask.
- Don't paste secrets into commands or files. This kit needs none.
- The kit was built and tested on Linux; macOS should work but is untested. On Windows, prefer WSL2; if you must stay native, use `python` instead of `python3` and expect some tools (`gio`, shell one-liners) to differ.
- Keep a short log of what you installed and changed; you'll summarise it at the end.

## Where the kit is

The user gives you either this file together with the kit (a git clone, a folder or a `.zip`), or this file inside the kit. The kit's layout:

```
ai-video-workflow-kit/
  README.md                this guide's human counterpart
  SETUP-FOR-AGENT.md       this file
  CUSTOMIZE.md             what to adapt, for the user
  workspace/               the workspace to copy: AGENTS.md, .agents/skills, Workflow/, templates, tools
  tests/, pyproject.toml   the kit's own test suite (not copied into the workspace)
```

If you only have this file, ask the user where the kit is (or to drop it in the folder you were opened in). Unzip a `.zip` into a temporary folder first.

## Step 1: Interview (one short round; skip what you can infer)

Detect the OS, CPU/GPU (`uname -a`, `nvidia-smi` if present), which agent you are, and which of `python3`, `node`, `ffmpeg`, `git` exist. Then ask, in one message, only what you can't tell:

1. **Where should the workspace live?** Suggest a folder on the drive with the most free space (video footage is large: tens of GB per video). Default suggestion: `~/Video-Workspace`.
2. **What do you edit in?** DaVinci Resolve, Premiere, Final Cut, Kdenlive, CapCut, HyperFrames Studio only, other.
3. **What do you record with, and do you use a green screen?** Phone, camera, screen recordings only; green screen yes/no. If the footage is HDR/HLG (recent iPhones and Android flagships), say so; it changes the delivery choices.
4. **Long-form, Shorts/TikTok/Reels, or both?**
5. **Your channel, in a sentence or two** (name, topic, who watches). Optional: you can also fill in `CHANNEL.md` later when you first plan a video.

Ask nothing else in this round (backups and trash tools come up in step 6). Record the answers; step 6 uses them.

## Step 2: Copy the workspace

Copy the contents of the kit's `workspace/` into the chosen folder (create it if needed), preserving structure and hidden folders (`.agents`, `.claude`, `.codex`):

```bash
mkdir -p "<workspace>" && cp -a "<kit>/workspace/." "<workspace>/"      # Linux/macOS
```

On Windows without WSL, use `robocopy "<kit>\workspace" "<workspace>" /E`. Copy `SETUP-FOR-AGENT.md` to `<workspace>/docs/SETUP.md` if it isn't there already (the workspace's `AGENTS.md` points to that path). From here on, work inside the workspace folder.

Then make skills and `CLAUDE.md` visible to Claude Code (relative symlinks; copies where symlinks aren't possible):

```bash
python3 Workflow/Tools/setup/link_skills.py
```

Optionally initialise git so the user can see and undo changes (ask first): `git init && git add -A && git commit -m "Video workflow starter"`. The workspace's `.gitignore` keeps footage, exports, caches and working folders out of git, but commit only now, at setup time; never `git add -A` in a workspace that holds videos without checking `git status` first (footage runs to tens of GB).

## Step 3: Check and install requirements

```bash
python3 Workflow/Tools/setup/check_setup.py
```

Install what's missing. Ask before system-level installs.

| Requirement | Why | Linux (Arch / Debian-Ubuntu / Fedora) | macOS (Homebrew) |
| --- | --- | --- | --- |
| **Python 3.10+** (required) | every tool | usually present | `brew install python` |
| **FFmpeg + ffprobe** (required) | probing, transcoding, analysis, renders | `pacman -S ffmpeg` / `apt install ffmpeg` / `dnf install ffmpeg` (Fedora needs RPM Fusion) | `brew install ffmpeg` |
| **Node.js 22+ and npm/npx** (required, HyperFrames needs ≥ 22) | HyperFrames motion graphics, renders, the lint gate | `pacman -S nodejs npm` / NodeSource or `nvm install 22` | `brew install node` |
| **git** (required) | skill installs, undo | `pacman -S git` / `apt install git` | `brew install git` |
| **yt-dlp** (recommended) | `video-study`, `video-ideas`, `video-packaging` (fetch captions, metadata, thumbnails; no login) | `pipx install yt-dlp` or the distro package | `brew install yt-dlp` |
| **faster-whisper** (recommended) | local transcription in `Workflow/Tools/study/study.py` | see "Transcription" below | same |
| **Pillow** (recommended) | thumbnail feed check (`Tools/packaging/feedcheck.py`) | `pip install pillow` in the venv below | same |
| **7-Zip** (recommended) | `video-closeout` archives | `pacman -S 7zip` / `apt install 7zip` (older releases: `p7zip-full`; check the package name) | `brew install sevenzip` |
| **A trash tool** (recommended) | moves files to the trash instead of deleting | `gio` (glib, usually present) or `trash-cli` | `brew install trash` |
| **Demucs** (optional) | music stem splitting, `Tools/stems/README.md` | see that README | same |

**Transcription.** Create one Python venv for the workflow's Python dependencies, outside system Python:

```bash
python3 -m venv Workflow/Tools/.venv
Workflow/Tools/.venv/bin/pip install faster-whisper pillow send2trash
```

Then tell `study.py` to use it: export `WHISPER_PY="<workspace>/Workflow/Tools/.venv/bin/python"` (put this in the shell profile or, for Claude Code, in `.claude/settings.local.json` under `env`). `WHISPER_MODEL` defaults to `small`, downloaded on first use (~500 MB); use `medium` or `large-v3` for better accuracy if the machine has a GPU, or a language-specific model for non-English narration. Test on a 10 s clip: `python3 Workflow/Tools/study/study.py transcribe <clip> /tmp/t.txt` (use a scratch folder rather than `/tmp` if the workspace has one).

## Step 4: Install the HyperFrames skills

The motion-graphics and rendering skills (`hyperframes`, `hyperframes-core`, `hyperframes-cli`, `hyperframes-animation`, `hyperframes-audio`, `hyperframes-creative`, `hyperframes-keyframes`, `hyperframes-registry`, `hyperframes-studio`, `media-use`) come from the open-source HyperFrames project and are **not bundled**, so the user always gets current versions. From the workspace root:

```bash
npx skills add heygen-com/hyperframes        # the skills.sh installer; interactive picker (nothing is preselected: choose the Core Skills group)
npx hyperframes doctor                       # checks Node, FFmpeg, Chrome for rendering; fix what it reports
```

An agent without a terminal picker can install one skill at a time with `npx skills add heygen-com/hyperframes --skill <name>` (bare name, e.g. `hyperframes`, `hyperframes-core`, `hyperframes-cli`, `hyperframes-animation`, `hyperframes-audio`, `hyperframes-creative`, `hyperframes-keyframes`, `hyperframes-registry`, `hyperframes-studio`, `media-use`), or use `npx hyperframes skills update` (installs the core set from the project's main branch; more workflows install on demand). Prefer the project-local form. These commands change often: confirm the current instructions with the Context7 MCP server or `npx ctx7@latest docs /heygen-com/hyperframes "install the skills for AI coding agents"` (or the README at `https://github.com/heygen-com/hyperframes`) if anything below fails.

Skills must end up in `<workspace>/.agents/skills/<name>/SKILL.md` (that is the workspace's canonical location; Codex reads it directly). After installing, find where they landed (`ls .agents/skills .claude/skills ~/.agents/skills ~/.claude/skills`). If an installer put them in a global folder or in `.claude/skills` only, **copy** (don't move; leave other projects' copies alone) the HyperFrames skill folders into `<workspace>/.agents/skills/`, then re-run `python3 Workflow/Tools/setup/link_skills.py`. Keep the workspace self-contained: don't rely on global skills.


## Step 5: Agent-specific wiring

- **Claude Code:** `.claude/settings.json` already runs the HyperFrames lint gate after every edit and before a turn ends. It calls `python3`; on Windows change it to `python`. `CLAUDE.md` links to `AGENTS.md`. Per-machine settings (env vars, permissions) go in `.claude/settings.local.json`, not in `settings.json`.
- **Codex:** `.codex/config.toml` mirrors the hooks; Codex asks the user to trust project hooks once in its TUI. Until then, run the lint by hand: `python3 Workflow/Tools/hyperframes-lint/hf_lint_hook.py check <project>`.
- **Another agent:** it should read `AGENTS.md` and load `.agents/skills/*/SKILL.md` on demand. If it supports hooks, wire `Workflow/Tools/hyperframes-lint/hf_lint_hook.py post|stop` the way `.claude/settings.json` does; if not, run `check` after editing a HyperFrames project.
- Pin a HyperFrames version only if a project needs one: write it into `Workflow/hyperframes-pin.txt` (default: latest).

## Step 6: Personalise

Use the interview answers. Keep edits small and tell the user what you changed.

1. **`Workflow/CHANNEL.md`:** fill in what you learned (channel, niche, viewer). Remove the `(not filled in)` line only if the profile is real; otherwise leave it and the skills will ask on the first video. Don't invent an audience.
2. **`Workflow/STYLE.md`:** the "starter default" rows are the original creator's working style. Read the user through them in one short list ("keep, change or drop?") only if they're keen; otherwise leave them and let the user edit as they go. Fill "Short-form" answers from the interview.
3. **Editor:** if the user doesn't use Resolve, rename `_Video-Template/04-Resolve` (and its `DRP-Backups` subfolder) to the editor's name, e.g. `04-Project-Files`, and update the folder table in `README.md` and any other mention. Grep for `04-Resolve` to find them.
4. **Delivery profile:** if the footage is HDR/HLG or high-frame-rate, note it in `Workflow/LESSONS.md` or the first video's `RECORD.md`; the defaults keep source resolution, cadence and colour.
5. **Green screen:** only if the user records on a green screen, walk through the `presenter-finishing` skill's stages together and note their keyer in `Workflow/STYLE.md`. Otherwise say the `presenter-finishing` skill is optional.
6. **Shorts:** if the user doesn't make shorts, nothing to do (the `short-*` skills stay dormant).
7. **Trash and backups:** confirm which trash tool works (`gio trash --version`, `trash --version`, or send2trash) and ask whether a second drive exists for footage backups; note the answer in `Workflow/STORAGE-POLICY.md`.

## Step 7: Verify

Run all of these and fix what fails:

```bash
python3 Workflow/Tools/setup/check_setup.py
python3 Workflow/Tools/tactics/tactics.py find --format long --stage hook | head        # tactics library loads
python3 Workflow/Tools/study/study.py 2>&1 | head -5                                    # prints usage
npx hyperframes doctor
ls .agents/skills .claude/skills                                                        # every skill visible
```

Then a small smoke test of the transcription path on any short clip the user has (or one you generate with `ffmpeg -f lavfi -i "sine=frequency=440:duration=3" ...`, which will transcribe as silence; that still proves the model loads).

## Step 8: Finish

1. Create `Workflow/.setup-done` containing the date, OS, agent, what was installed and what was skipped.
2. Tell the user, briefly: what's installed, what's missing or optional and what it would unlock, where the workspace is, and how to start: open the agent in the workspace folder and say what they want ("I have an idea for a video about …", "plan some shorts", "edit the footage in `Incoming/`"). Mention the three files they should look at first: `Workflow/CHANNEL.md`, `Workflow/STYLE.md`, `AGENTS.md`.
3. Mention that the tactics library starts with a few example cards and grows from their own studies and results (`video-study`, `video-performance`).

## Reference: what's in the workspace

| Path | What it is |
| --- | --- |
| `AGENTS.md` (`CLAUDE.md` links to it) | the project instructions every agent reads first |
| `.agents/skills/` | the workflow skills: `video-ideas` → `video-brief` → `youtube-editing-workflow` → `retention-review` → `video-packaging` → `video-closeout` → `video-performance`; `video-intro`, `video-study`, `video-lessons`, `presenter-finishing`; `short-plan` → `short-edit` → `short-publish` (plus the HyperFrames skills you install in step 4) |
| `Workflow/CHANNEL.md`, `STYLE.md`, `LESSONS.md`, `CURRENT-EDIT.md` | the user's channel, taste, learned rules and the active video |
| `Workflow/Tactics/` | the tactics library (idea, title/thumbnail, retention and short-form cards; a few examples to start), searchable with `Tools/tactics/tactics.py` |
| `Workflow/Pipelines/` | playbooks: `Recording-Prep.md`; add your own |
| `Workflow/Tools/` | `study` (fetch/analyse/transcribe videos), `ideas` (outlier research), `packaging` (thumbnail check), `closeout` (verified archives), `tactics`, `stems`, `hyperframes-lint`, `setup` |
| `_Video-Template/`, `_Short-Template/` | folder templates copied per video / short |
| `Shared-Assets/` | reusable music, SFX, fonts, brand files, licences (empty) |
| `Videos/`, `Incoming/` | the user's videos (empty) and the drop folder for new recordings |

## Troubleshooting

- `npx hyperframes …` fails on Node: `node --version` must be ≥ 22.
- Renders complain about Chrome or fonts: run `npx hyperframes doctor` and follow its output; install the fonts the composition uses.
- `study.py transcribe` says `faster_whisper` is missing: set `WHISPER_PY` to the venv's interpreter (step 3).
- The lint hook does nothing: check `python3` exists on the hook's PATH and that the project has a `hyperframes.json` (or `index.html` + `compositions/`). Projects inside `scratch/` folders are skipped on purpose.
- A skill isn't picked up: it needs `SKILL.md` with front-matter in `.agents/skills/<name>/` and a link in `.claude/skills/` (run `link_skills.py`).
