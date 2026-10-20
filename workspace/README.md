# Video production home

An AI-agent-driven workflow for planning, editing and publishing YouTube videos (long-form and Shorts/TikTok/Reels). Your agent (Claude Code, Codex or any agent that reads `AGENTS.md`) follows the project instructions in [AGENTS.md](AGENTS.md) (`CLAUDE.md` links to it) and the project-local skills in `.agents/skills/`.

First time here? Open your agent in this folder and say "set this workspace up". It follows [docs/SETUP.md](docs/SETUP.md).

- **New video idea?** Just describe it; the `video-brief` skill talks it through with you and sets up the folder. No idea yet? `video-ideas`.
- **Found a useful video, file or GitHub skill?** Send the link or file; `video-study` analyses it and proposes concrete improvements.
- **Video finished?** Say it's final; `video-closeout` records it, archives the raw footage and cleans up (with your approval).
- **Shorts?** `short-plan` → `short-edit` → `short-publish`.

What's active: [Workflow/CURRENT-EDIT.md](Workflow/CURRENT-EDIT.md). Your preferences: [STYLE.md](Workflow/STYLE.md). Your channel: [CHANNEL.md](Workflow/CHANNEL.md). What you've learned: [LESSONS.md](Workflow/LESSONS.md). The tactics library (ideas, titles/thumbnails, retention, shorts): [Workflow/Tactics/INDEX.md](Workflow/Tactics/INDEX.md).

## Where things go

New videos start as a copy of `_Video-Template` (the `video-brief` skill does this): `Videos/YYYY-MM-DD-short-title/`.

| Folder | Contents |
|---|---|
| `Videos/<video>/BRIEF.md`, `RECORD.md` | The plan, then the running record (state, decisions, where everything is, how to restore) |
| `01-Raw` | Original footage, untouched. Packed into verified 7-Zip archives in `12-Archive` when the video is closed |
| `02-Audio`, `03-Assets` | Voiceovers; stock clips, graphics, music and effects used by this video |
| `04-Resolve` | Exported editor project snapshots (rename it for your editor if you like) |
| `05-Exports/Review`, `Final` | The current review render; the finished files with credits and checksums |
| `06-Publishing` | Thumbnail, subtitles, title, description, upload notes |
| `07-Cache` | Regenerable caches and proxies |
| `08-Analysis`, `09-Footage-Library` | Transcripts, provenance, edit timelines; readable topic folders of the footage |
| `10-Project` | The editable project (HyperFrames composition etc.) |
| `11-Work` | Dated working folders; `11-Work/scratch/` for experiments (cleaned at milestones) |
| `12-Archive` | Closed-out archives: raw footage, outtakes, packed logs, sample frames |
| `Workflow/` | General knowledge only: preferences, lessons, playbooks, tactics, tools |
| `Shared-Assets/` | Reusable music, effects, fonts, brand files and licences |
| `Incoming/` | Drop folder for new recordings; copies go to the trash once safely in `01-Raw` |

Storage rules: [STORAGE-POLICY.md](Workflow/STORAGE-POLICY.md). Assistants never permanently delete. Approved removals go to the trash, and you empty it when you want the space back.

Backups: keep a second copy of irreplaceable footage (anything in `01-Raw` and the `12-Archive` 7z files) on another drive.

## Editing software

The workflow is editor-agnostic: the agent works from transcripts, timelines and HyperFrames (HTML-based motion graphics and renders). Use whichever editor you like for the cut, colour and final delivery. If you use DaVinci Resolve, keep its project library outside the video folders and export milestone project snapshots to `04-Resolve`; a project file holds project data, not footage, so avoid moving media after importing it.
