---
name: youtube-editing-workflow
description: Use when editing or polishing a video in this YouTube workspace — cuts, takes, motion graphics, revisions, renders, final exports — or when resuming an edit in a new session. Long-form only; for Shorts, TikTok or Reels use the short-* skills.
---

# Conversational video editing

Paths are relative to the workspace root (where `AGENTS.md` is). This skill coordinates the workflow; the HyperFrames skills do the motion and rendering work.

## Start here

1. `Workflow/CURRENT-EDIT.md` → the active video's `RECORD.md` (and `BRIEF.md`) in `Videos/<video>/`.
2. `Workflow/STYLE.md` (how the user works and what they like) and the headings of `Workflow/LESSONS.md`. Read the lessons that apply.
3. If the video has a presenter or green screen, the stage you're on in the `presenter-finishing` skill.
4. For motion work, `hyperframes/SKILL.md` and the skills it routes to. Check `Workflow/COMPONENTS.md` before building a treatment that may already exist. Read a project's README before regenerating anything: rebuilding HTML can overwrite manual Studio edits.

Other skills, in the order a video uses them:
- `video-ideas` → `video-brief` → this skill (with `video-intro` for the hook);
- `retention-review` before showing the user a cut, and when asked what would make it better;
- `video-packaging` (final thumbnails and titles) → `video-closeout` → `video-performance` after publishing.

Also: learning from a link, file or GitHub skill → `video-study`; something worth remembering → `video-lessons`.

## Turning direction into edits

Resolve ordinary descriptions (an explanation, a repeated take, a word, a moment) to source IDs and times with the transcript and timeline, and show uncertainty rather than guessing. Keep unique information inside partly useful takes. For a new scene, state its intent briefly (viewer takeaway, evidence phrase, assets, placement, timing); a clear small revision needs no brief. Keep approved surroundings stable. Establish a new direction on one representative scene before applying it across a long video.

Tools: local transcription (`python3 Workflow/Tools/study/study.py transcribe <media> <out>`, `--words` for word times) gives words and timing; map them onto the cut yourself and re-check after every cut change. Suggested labels and repeat comparisons are proposals only. HyperFrames renders the edit; use the hyperframes skills' current CLI unless the project pins a version (see `AGENTS.md`).

## Working files

Experiments, probes and comparison clips go in `Videos/<video>/11-Work/scratch/`. Keep one current review render. At each milestone, update `RECORD.md` (state, decisions with the user's words, next step) and trash your own scratch and replaced review renders (anything else only after the user sees the list; `Workflow/STORAGE-POLICY.md`). Keep `CURRENT-EDIT.md` to a few lines.

## Retention tactics

Every video uses the retention tactics that fit it. Read the brief's shortlist (`BRIEF.md` → "Tactics") and the core checks in `Workflow/Tactics/INDEX.md`, not the whole library; open a tactic with `python3 Workflow/Tools/tactics/tactics.py show <slug>` (the working card), `--full` for the whole card. The library has one folder per tactic with what it does, how we apply it, when to skip it, a check and its sources. Examples are reference points, not templates.
- **While building scenes,** apply the tactics chosen in `BRIEF.md` → "Tactics"; open each tactic's `TACTIC.md` when you get to it.
- **When suggesting improvements** (or the user asks what would make a passage better), use `retention-review`. It names the tactic behind each suggestion, so the user can look at its examples.
- A tactic that fights the brief's viewer experience is skipped. Natural pacing and complete explanations (`STYLE.md`) outrank any tactic.
- Record the tactics actually used, with timestamps, in `RECORD.md` → "Tactics used and results".

Before a review render: run the hook check (`video-intro`), then `retention-review` (eye trace, still stretches, pauses, open loops, what-you'd-miss). Fix what's clearly broken; list the rest as suggestions for the user.

## Quality

Check the encoded output for motion, joins, sync, legibility, colour and playback; a screenshot isn't enough. Internal proxies are fine for speed, but label them. Deliver in the verified original-resolution/cadence/HDR profile unless the user wants another.
