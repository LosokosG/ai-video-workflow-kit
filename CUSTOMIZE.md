# Customising the kit

The kit is a set of plain text files. Your agent can change any of them for you; say what you want ("I don't use Resolve", "my videos are 9:16 only", "drop the green-screen material").

## What's personal to the original creator (change freely)

| Where | What to look at |
| --- | --- |
| `Workflow/STYLE.md` | rows marked *starter default*: pacing, "videos shouldn't all look the same", subtitles, transitions. Replace with your own taste. |
| `Workflow/LESSONS.md` | every lesson is `starter default`. Keep, edit, or retire (`video-lessons` handles this). Numbers like music loudness are starting points from one mic and room. |
| `AGENTS.md` → "Editorial and quality defaults" | the same taste defaults; `STYLE.md` overrides them. |
| `Workflow/CHANNEL.md` | empty; filled from your answers. Examples in the skills often use AI-topic videos (the workflow was built on an AI channel); swap in your niche. |
| `Workflow/Tactics/` | a few example cards from the original creator's edits, all `candidate`: you haven't tried them yet. They move to `used` / `proven` as your videos give evidence (`video-closeout`, `video-performance`). Add your own with `video-study` or by hand. |

## Setup-dependent parts

| Part | Depends on | If yours differs |
| --- | --- | --- |
| `_Video-Template/04-Resolve` | DaVinci Resolve project snapshots | rename the folder for your editor (and the mentions in `README.md`, `STORAGE-POLICY.md`) |
| `presenter-finishing` skill | green-screen presenter footage, a keyer, HDR/HLG phone footage | ignore it if you don't key or grade presenter footage; its stages (probe → key → integrate → colour → render → sound → deliver) are useful anywhere |
| Delivery profile | the default keeps source resolution, frame rate and colour | tell the agent your target (e.g. 1080p SDR H.264) and it records it in the video's `RECORD.md` |
| Local transcription | `faster-whisper` model `small` | `WHISPER_MODEL=medium` (or `large-v3`, or a language-specific model) for better accuracy |
| Trash policy | `gio trash` on Linux | the agent uses `trash` on macOS or `send2trash` elsewhere; it never deletes permanently |
| Hooks | `python3` on PATH | on Windows change `python3` to `python` in `.claude/settings.json` and `.codex/config.toml` |

## Things you can turn off

- **Shorts:** don't use the `short-*` skills; nothing else depends on them.
- **Retention tactics:** `AGENTS.md` says every long video uses fitting tactics. If you'd rather not, change that line and `STYLE.md`.
- **Lint gate:** remove the `hooks` block from `.claude/settings.json` / `.codex/config.toml` if you don't use HyperFrames.
- **Two-agent handoffs:** `AGENTS.md` → "Agent roles" is optional; one agent can do everything.

## Adding your own

- A new skill: a folder `.agents/skills/<name>/SKILL.md` with `name` and `description` front-matter, then `python3 Workflow/Tools/setup/link_skills.py`.
- A new tactic: ask the agent to add it via `video-study`; it creates `Workflow/Tactics/<library>/<slug>/TACTIC.md` and rebuilds the index with `Workflow/Tools/tactics/build_index.py`.
- A new pipeline or playbook: add `Workflow/Pipelines/<Name>.md` (or a folder with a `PLAYBOOK.md`) and mention it in `AGENTS.md`.

## Keeping it clean

Work products live in `Videos/<video>/`; `Workflow/` holds only general knowledge you want kept. The agent never permanently deletes; it moves things to the trash and you empty it. Keep a second copy of your raw footage on another drive.
