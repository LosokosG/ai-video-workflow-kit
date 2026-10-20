---
name: short-edit
description: Use when editing, cutting, reframing, captioning or rendering a Short, TikTok or Reel, including turning a passage of one of our long videos into a vertical short.
---

# Editing a short

Short-form only. The plan is in the short's `Videos/Shorts/<short>/SHORT.md` (from `short-plan`); without one, run `short-plan` first. Tactics: the plan's shortlist (`SHORT.md` → Tactics) plus the core checks in `Workflow/Tactics/SHORTS-INDEX.md`; open one with `python3 Workflow/Tools/tactics/tactics.py show <slug>`.

## Build

1. **Project:** a HyperFrames project in `<short>/project/`, 1080×1920, at a constant 30 or 60 fps.
   - Shorts deliver SDR by default (the user can change it). A short is a separate project from any long-form project, so a long-form renderer pin doesn't apply to it.
   - Use the current HyperFrames CLI and follow the hyperframes skills, but skip their intent interview (`SHORT.md` is the brief), and remove the boilerplate `CLAUDE.md`/`AGENTS.md` that `hyperframes init` writes into the project. The lint gate applies (`AGENTS.md`).
2. **Material:**
   - **Native:** footage from `raw/`. Probe phone clips first: real frame rate, and whether they're HDR.
   - **Cut from long:** rebuild from the long video's layers (the keyed presenter, screen recordings, scene HTML), never by cropping the 16:9 master (`shorts/rebuild-from-layers`).
   - **Presenter resolution:** a presenter shown large needs a re-key from the original footage at that size.
3. **Edit:**
   - Frame 0 already belongs to the hook: something is moving or on screen, no dead air.
   - Burn in the text hook and hold it long enough to read.
   - Full captions timed from word timestamps mapped onto the cut, with words a cut splits flagged. Redo the mapping after every cut change.
   - Trim pauses from word timestamps, keeping one deliberate beat before the payoff.
   - Prefer punch-ins and drift to hard jumps.
   - End on the payoff; add a loop only if it was planned.
   - Build new components as 2–3 variants on a real beat; the user picks, and the chosen one goes into `Workflow/COMPONENTS.md`.
4. **Sound:**
   - The voice comes first and stays clear on a phone speaker.
   - Measure the music bed against speech and check it on a phone-speaker simulation. A workable start is ~18–20 LU under speech; answer "music too loud" with a measured reduction from the reviewed version.
   - Effects fall between words, never on the hook words.
   - Music is licensed, and the licence recorded.
5. **Safe zones:** keep the text hook, captions, faces and the key result clear of each app's buttons and caption area. Check the current overlay layout of every target app rather than trusting old numbers.

## Check before showing the user

- **QC on the encoded file:** ffprobe profile, a full decode without errors, loudness and true peak, and frame 0.
- **Safe zones:** frames at 0.0, 1.5 and 3.0 s against each app's overlay.
- **Muted first seconds:** with the sound off, picture and text alone say what the short is and why to stay.
- **Beat timings:** `python3 Workflow/Tools/study/study.py analyze <render> <out.json>` and `transcribe --words` confirm the planned beat times, and that nothing sits still in the first 3 s.

Write the results in `SHORT.md` → Edit. Show the user a labelled review render; it becomes the master once approved.

Next: `short-publish`.
