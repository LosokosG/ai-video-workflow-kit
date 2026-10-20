# AI video workflow kit

A workspace that turns an AI coding agent (Claude Code, Codex, or any agent that reads `AGENTS.md`) into a YouTube editor's assistant: planning, retention review against measurements, packaging, and close-out, without the agent forgetting the channel's rules between sessions.

I built this workflow in September and October 2026 for my own channel; this is the shareable version, with course-derived material and third-party skills removed.

## The problem

Editing with an agent works for one session and then falls apart. The agent forgets which intro style the channel uses, re-asks the same questions, judges pacing by feel, says a render is "done" from a screenshot, and deletes things it shouldn't. The fix here is not a bigger prompt. Every rule lives in a file the agent reads at the right step, and anything measurable gets measured by a script.

## How it works

The workspace (`workspace/`) is a folder you open your agent in:

- **`AGENTS.md`** is the standing instruction: where things live, what the agent may and may not delete, quality defaults, the order of the stages.
- **One skill per stage** in `.agents/skills/`: `video-ideas` → `video-brief` → `video-intro` → `youtube-editing-workflow` → `retention-review` → `video-packaging` → `video-closeout` → `video-performance`, a short-form chain (`short-plan` → `short-edit` → `short-publish`), plus `video-study`, `presenter-finishing` and `video-lessons`. The agent loads only the skill for the job at hand.
- **Deterministic tools the skills call** (`workspace/Workflow/Tools/`, Python, mostly stdlib):
  - `study/study.py` measures a video: hard cuts, new-element onsets, still stretches, loudness, pauses and speech rate, local transcription with word times, contact sheets stamped with source time. `video-intro` and `retention-review` use it to check a hook or a cut against numbers instead of impressions.
  - `ideas/outliers.py` scores videos by views ÷ their channel's median from public `yt-dlp` listings (no login), to find ideas that outperformed.
  - `packaging/feedcheck.py` puts a thumbnail candidate into a mock YouTube feed among current niche thumbnails, in greyscale and at small sizes.
  - `hyperframes-lint/hf_lint_hook.py` runs as a Claude Code / Codex hook after every edit and before the turn ends, and blocks the agent while a HyperFrames project has lint errors.
  - `tactics/` searches and indexes the tactics library; `closeout/archive_raw.py` packs raw footage into hash-verified 7-Zip archives; `setup/` checks the machine and links the skills.
- **A learning loop:** `video-lessons` drafts rules from what happened in a session (with the evidence inline) into `Workflow/LESSONS.md`; the user confirms the scope; the next session reads the headings first. Preferences go to `STYLE.md`, one-video facts to that video's `RECORD.md`.

## Design decisions

- **Skills per stage instead of one giant prompt.** Each stage loads a short, specific instruction and the files it needs; nothing else competes for the agent's attention.
- **Deterministic tools for anything measurable.** Still stretches, first-word time, loudness and outlier scores come from scripts with documented thresholds and caveats; the agent interprets, it doesn't estimate.
- **A lint hook that fails closed, with an explicit accept-list.** Errors always block (exit 2 feeds them back to the agent). A deliberate warning can be accepted only by a line in `<project>/.hyperframes-lint-accept` with a reason, and the agent must tell the user. A broken lint run never blocks editing, and the stop hook can't loop.
- **Works with Claude Code and Codex.** Skills live once in `.agents/skills/`; `link_skills.py` exposes them to Claude Code. Hooks are wired in both `.claude/settings.json` and `.codex/config.toml`.
- **Nothing is ever permanently deleted.** Removals go to the OS trash, with the exact list shown to the user first.

## Honest limits

- It was built around my own channel's workflow (an AI-topic channel, long-form videos with green-screen presenter footage) and tested on Linux only. Defaults about taste and hardware are labelled as starter defaults.
- Motion graphics and rendering depend on [HyperFrames](https://github.com/heygen-com/hyperframes), an external project the setup installs from upstream (`npx skills add heygen-com/hyperframes`). It is not vendored here.
- Not included: my green-screen presenter pipeline (keying scripts and playbook that depend on code and settings I haven't published), the short-form and business playbooks and the tactic cards distilled from a paid course and from other creators' videos, and an adapted third-party overlay skill. The tactics library ships with six example cards written from my own edits.
- There are no claims here about channel performance. The kit records your numbers when you share them; it doesn't promise any.
- The tests cover the deterministic code only. Skills are instructions for an agent; their effect isn't unit-testable. `feedcheck.py` and the ffmpeg / yt-dlp / whisper paths of `study.py` have no automated tests.

## Setup

Open your agent in this folder and say: "Read SETUP-FOR-AGENT.md and set this up for me." The agent asks a few questions (where the workspace goes, what you edit and record with), copies `workspace/` there, installs what's missing (asking before anything system-wide), installs the HyperFrames skills, and personalises `CHANNEL.md` and `STYLE.md`. After that, open the agent in the workspace and talk: "I have an idea for a video about …", "review this cut", "plan some shorts". [CUSTOMIZE.md](CUSTOMIZE.md) lists what to adapt.

Requirements: Python 3.10+, FFmpeg, Node.js 22+, git; recommended yt-dlp, faster-whisper, Pillow, 7-Zip.

Running the tests:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

## Layout

| Path | What it is |
| --- | --- |
| [`SETUP-FOR-AGENT.md`](SETUP-FOR-AGENT.md) | step-by-step setup for the agent (copied to `workspace/docs/SETUP.md`) |
| [`CUSTOMIZE.md`](CUSTOMIZE.md) | what to change for your own channel and setup |
| [`workspace/AGENTS.md`](workspace/AGENTS.md) | the project instructions every agent reads first |
| `workspace/.agents/skills/` | the 14 workflow skills, one folder each |
| `workspace/.claude/`, `workspace/.codex/` | lint-gate hooks for Claude Code and Codex |
| `workspace/Workflow/` | `CHANNEL.md`, `STYLE.md`, `LESSONS.md`, `Ideas.md`, storage policy, recording prep, the tactics library and the tools |
| `workspace/_Video-Template/`, `workspace/_Short-Template/` | folder and record templates copied per video / short |
| `workspace/Videos/`, `workspace/Incoming/`, `workspace/Shared-Assets/` | empty folders for your videos, new recordings and reusable assets |
| `tests/` | pytest suite for the tools and a repo validator (skills, links, tactic cards) |

## License

MIT, see [LICENSE](LICENSE). Third-party tools the kit calls (HyperFrames, FFmpeg, yt-dlp, faster-whisper, Demucs, 7-Zip) are installed separately under their own licences.
