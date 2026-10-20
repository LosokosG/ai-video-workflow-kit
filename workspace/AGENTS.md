# Video editing workspace: instructions for AI agents

`CLAUDE.md` is a relative symlink to this file (Claude Code reads `CLAUDE.md`, Codex and most other agents read `AGENTS.md`); edit this one and keep the symlink. Skills live in `.agents/skills/` (canonical, read by Codex and others), and `.claude/skills/<name>` links to each one for Claude Code. Don't install skills globally or duplicate them.

## First run

If `Workflow/.setup-done` doesn't exist, this workspace hasn't been set up yet: follow `docs/SETUP.md` (install requirements, interview the user, fill in `CHANNEL.md` and `STYLE.md`, create `Workflow/.setup-done`). Don't start video work before that. If `Workflow/CHANNEL.md` still says `(not filled in)` after setup, ask for the channel profile when the first video is planned (`video-brief`, `video-ideas`).

Examples in the skills and tactics often use AI-topic videos for illustration (the workflow was built while editing AI and software videos). Adapt them to the user's niche; they are not the user's subject.

## Start here

**Short-form work** (Shorts/TikTok/Reels) reads only `STYLE.md` → "Short-form" and the `short-*` skills below; it skips the long-form steps 1 and 3 and the long-form rules marked below.

1. `Workflow/CURRENT-EDIT.md` names the active video → read its `Videos/<video>/RECORD.md` (and `BRIEF.md`).
2. `Workflow/STYLE.md`: how the user works and what they like. `Workflow/CHANNEL.md`: which channel a video is for and its audience.
3. The headings of `Workflow/LESSONS.md`: read the lessons that apply to the task.
4. Then the skill for the job. A video moves through them in this order:
   `video-ideas` → `video-brief` (+ `video-packaging` drafts, `video-intro` plan) → recording → `youtube-editing-workflow` (+ `presenter-finishing`, `hyperframes`, `video-intro`) → `retention-review` → `video-packaging` final → `video-closeout` → `video-performance`.

   **Short-form** (YouTube Shorts / TikTok / Reels) is a separate pipeline: `short-plan` → `short-edit` → `short-publish`, using `Workflow/Tactics/SHORTS-INDEX.md` and `Videos/Shorts/`. Long-form work never loads it, and it never loads long-form context unless that genuinely helps the short at hand. Recording prep shared by both: `Workflow/Pipelines/Recording-Prep.md`.

   Alongside: `video-study` (learning from a link, file or GitHub skill) and `video-lessons` (recording what we learned). When choosing a look, also read `Shared-Assets/Brand/README.md`.

**Motion graphics and rendering** use the HyperFrames skills (`hyperframes`, `hyperframes-core`, `hyperframes-cli`, …), installed from upstream (`docs/SETUP.md`). If a project must stay on one HyperFrames version (for example because it needed a local patch), write that version in `Workflow/hyperframes-pin.txt`; the hyperframes skill's "keep the CLI current" step must not upgrade a pinned project.

**HyperFrames lint gate.** After editing a HyperFrames project, its lint findings must be fixed. Project hooks run the check after every edit and before a turn ends and feed the findings back: `.claude/settings.json` for Claude Code, `.codex/config.toml` for Codex (Codex asks the user to trust project hooks once in its TUI; until then, and whenever unsure, run it by hand: `python3 Workflow/Tools/hyperframes-lint/hf_lint_hook.py check <project>`). Errors must be fixed. A deliberate warning can be accepted in `<project>/.hyperframes-lint-accept` (`<code> <elementId>  # reason`), and the user is told.

**One brief per video.** Planning a video starts with `video-ideas` / `video-brief`, not the hyperframes skill's intent interview or a generic brainstorming skill. Once `Videos/<video>/BRIEF.md` (or a short's `SHORT.md` → Plan) exists, it's the creative brief; skip the hyperframes skill's own intent interview and pitch round.

The default focus is editing existing footage. Recording, transfer and intake automation are the user's own setup; don't build them unless asked.

## Agent roles

One agent can do every step. If the user runs two agents (for example one that asks planning questions and one that does the creative work), the planner hands over a brief in this shape, saved as `Videos/<video>/11-Work/briefs/<YYYY-MM-DD>-<topic>.md`: the user's own words · goal · feel · answers to the planner's questions · must keep · limits · where things are · what to hand back. Choices about *how* (layout, motion, tools) stay with the creative agent unless the user specified them. Never launch a background agent with permission checks disabled.

**Model routing for subagents:** use your strongest available model for creative work, synthesis, reviews and anything that gates a result. A cheaper model is fine for mechanical work: fixing lint findings, moving files, rebuilding indexes, checking links, writing prepared data into files, gathering data, checking platform facts, and the first reading pass of a study.

## Creative approach

- Videos should not all look the same. Carry forward know-how, not a fixed look. Propose 2–3 directions for new work, recommend one and explain why; the user chooses. The channel's brand marks (logo, colours, type once chosen) stay consistent; composition, look, mood and sound change per video.
- Every long video uses the retention and title/thumbnail tactics that fit it (`Workflow/Tactics/INDEX.md`; shorts use `SHORTS-INDEX.md`). Choose them in the brief, apply them in the edit, and name them when suggesting improvements. Their examples are reference points, not templates.
- Ask the user for anything that would make the result better (a re-take, an empty green-screen plate, better light, a logo file, the MP4 of a reference) and say why it helps.
- Settings from past videos are defaults for their context (camera, light, mic, software). Check that the context matches, and use a better method when one exists.
- Keep candidate looks separate from approved ones; approval is per video unless the user says otherwise.

## Editorial and quality defaults (long-form; short-form rules are in the `short-*` skills)

These are the starting defaults. `Workflow/STYLE.md` is the user's own version and overrides them.

- Keep useful introductions, conclusions and off-script explanations; no runtime cap or aggressive pacing unless the user wants one. Unused takes stay addressable by source and timestamps (in the archives once a video is closed).
- Fluid movement between coherent layouts; hard cuts only when needed; graphics-only sections are fine; consistent backgrounds and window edges within a video; selective burned-in subtitles.
- Green screen: verify a representative key in motion (hair and edge detail, spill, flicker, integration, colour) before calling it ready.
- Finished work needs polished typography, coherent colour, readable layouts, purposeful motion, natural audio joins and verified playback. A screenshot can't establish motion, sync or HDR quality.
- Proxies and short probes are fine for speed but must be labelled. Never pass a proxy off as a finished render. Keep source resolution, cadence and colour; never call a re-encode lossless.
- Transcript, scene and timing suggestions are proposals; verify them against the source.
- Translate normal spoken direction into concrete source ranges and scene choices; ask only when an open choice changes the result. Continue authorised work without re-asking. Don't rebuild generated HTML over manual Studio edits.
- Keep the video's `RECORD.md` current. Distinguish implemented, technically verified and user-approved.

## Files and storage

Follow `Workflow/STORAGE-POLICY.md`. In short:
- Everything about one video lives in `Videos/<video>/`; `Workflow/` holds only general knowledge the user wants kept.
- Experiments go in `Videos/<video>/11-Work/scratch/`, and only one current review render is kept.
- Originals are never lost: loose in `01-Raw` while working, in hash-verified 7-Zip archives in `12-Archive` after close-out. Before loose originals go to the trash, ask whether a second copy exists on another drive.
- Assistants never permanently delete; removals go to the OS trash (`gio trash` on Linux, `trash` or Finder on macOS, the Recycle Bin on Windows) and the user empties it. Without asking, an assistant may trash only what it generated itself in the current video's `11-Work/scratch/` (or the current short's `scratch/`) and review renders it made that a newer verified one replaced. Everything else needs the user to see the exact list first. Never bundle a deletion into a compound command with other steps.

## Learning

Record lessons with `video-lessons` (rule and evidence together in `Workflow/LESSONS.md`); technique detail goes in a playbook under `Workflow/Pipelines/` (one file per technique area, created when needed); confirmed preferences in `Workflow/STYLE.md`; one-video facts in that video's `RECORD.md`. Studies of outside videos and skills live in `Workflow/Studies/` (created on first use); the tactics they teach (ideas, titles/thumbnails, retention) go one per folder into `Workflow/Tactics/`. This is file-based memory the assistants share, not model training.

## Current documentation

Look up current library, framework, SDK, API and CLI-tool documentation (including configuration and library-specific debugging) instead of relying on memory: use the Context7 MCP server if it's connected, or the `ctx7` CLI (`npx ctx7@latest library <official-name> "<specific question>"`, then `npx ctx7@latest docs <library-id> "<specific question>"`). Never include secrets. General programming, business-logic debugging and ordinary file operations don't need a lookup.
