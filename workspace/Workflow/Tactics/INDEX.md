# Tactics library

This library holds the tactics for finding video ideas, getting a video clicked and keeping viewers watching to the end. Each tactic lives in its own folder:

```
<library>/<slug>/TACTIC.md       what · why · how we apply it · use when / skip when · check · source · used in
```

There are four libraries:
- `ideas/`: finding and vetting video ideas.
- `titles-thumbnails/`: packaging.
- `retention/`: hook, structure, visuals and editing, sound, ending.
- `shorts/`: short-form tactics (listed in `SHORTS-INDEX.md`).

The kit ships a handful of example cards written from its author's own edits. They show the format and seed the core checks; the library grows from your own studies (`video-study`) and your own results. Tactics are **reference points**, not templates: adapt a tactic to the video, and never reuse another creator's footage, music or branding.

## Using it on every video

The skills use it at each stage:
- `video-ideas`: idea tactics.
- `video-packaging`: titles and thumbnails.
- `video-brief`: choosing each video's tactics.
- `video-intro`: the hook.
- `youtube-editing-workflow`: applying the tactics.
- `retention-review`: suggestions, each naming its tactic (`retention/<slug>`).
- `video-performance`: results.

The chosen tactics go into `BRIEF.md` → "Tactics", each with where it lands and why it fits.

- **Pick, don't stack:** skip any tactic that fights the video's viewer experience. Natural pacing and complete explanations (`STYLE.md`) outrank any tactic.
- **After publishing:** the video's `RECORD.md` lists the tactics used, with timestamps. When the user shares YouTube Studio numbers (the retention graph, CTR), add the result to each tactic's "Used in".

<!-- pick-list:start -->
## Pick lists by stage

Load only the stage you are working on, plus the core checks below. To narrow further, use `python3 Workflow/Tools/tactics/tactics.py find --format long --stage <stage> [--face …] [--mode …] [--text …]`, then `tactics.py show <slug>` for the working card. Once a brief or plan has chosen its tactics, later steps read that shortlist, not these lists. Rebuilt by `build_index.py`; don't edit by hand.

| Stage | Pick list | Tactics |
| --- | --- | --- |
| Idea | [`picks/long-idea.md`](picks/long-idea.md) | 1 |
| Title and thumbnail | [`picks/long-title.md`](picks/long-title.md) | 1 |
| Hook (intro) | [`picks/long-hook.md`](picks/long-hook.md) | 1 |
| Structure and script | [`picks/long-structure.md`](picks/long-structure.md) | 1 |
| Sound | [`picks/long-sound.md`](picks/long-sound.md) | 1 |

### Core checks (3): apply every time

- `measure-the-hook` (Hook (intro)): Measure the first 30 s (first word, promise, proof, stills) before showing a cut
- `keep-useful-explanations` (Structure and script): Cut stumbles and dead air, never useful explanations; no runtime target
- `show-the-real-result` (Title and thumbnail): Put only results on the thumbnail that the video really shows, and show them early
<!-- pick-list:end -->

## Maintaining the library

**Status:**
- `candidate`: learned, not yet used in a video.
- `used`: used in at least one of your videos.
- `proven`: support in 2–3 of your videos, or a clean test & compare winner that isolates it, or the user's verdict with the evidence shown (`video-performance`).
- `dropped (reason)`: after repeated poor results, or when the user says so.
- `skip by default (reason)`: kept for reference, but it conflicts with a stated preference.

**Adding** (`video-study`):
- A new tactic gets its own folder, with status `candidate`. Rebuild the pick list with `python3 Workflow/Tools/tactics/build_index.py`; group notes live in `index-notes.md`.
- If the tactic already exists, add the new source to its `TACTIC.md` instead.

**Changing a status:** update the tactic's status line and its "Used in", then rebuild the index.

`TACTIC.md` shape (line 3 is parsed by `tactics.py`; missing tags mean formats long, face any, mode any, core no):
```
# <Name>
`<library>` · [formats: long|short|long, short ·] [role: <check|attention|curiosity|benefit|credibility|process> (titles-thumbnails) ·] [face: presenter|faceless|mixed ·] [mode: native|cut ·] [core: yes ·] stages: <…> · status: candidate · source: <source name>

**Pick:** <imperative, ≤ 90 characters; shown in the pick list>

**What:** … **Why it works:** … **How we apply it:** … **Use when / skip when:** … **Check:** …
**Related:** <other tactics>
**Source:** <where it came from: a URL with timestamps, a study, or one of your own videos>

## Used in
(date · video · where · result)
```
