---
name: retention-review
description: Use when asked what would make a video, script, rough cut or review render better, when reviewing an edit for pacing or viewer retention, or before telling the user an edit is ready to look at. Long-form only; for Shorts, TikTok or Reels use the short-* skills.
---

# Retention review

A structured pass that turns the tactics library into specific, evidenced suggestions. It works on a script or outline, a rough cut, or a review render. Suggest; don't apply, unless the user asked for the changes. Natural pacing and complete explanations (`STYLE.md`) outrank every tactic. Never propose cutting a useful explanation to hit a number.

## Inputs

- `BRIEF.md` (the viewer experience, the tactics chosen, the hook and packaging blocks) and `RECORD.md`.
- **No brief or package?** Use the user's description or the spoken promise, and flag the missing package.
- The render or script.
- The audio recipe (cue list, music map).
- A full transcript: `study.py transcribe <render> <out.txt>`. Correct misheard names against the source transcripts before quoting.
- A full contact sheet: `study.py sheet <render> <out.jpg> 2`.

Run the commands from the workspace root as `python3 Workflow/Tools/study/study.py …`, with outputs in `Videos/<video>/11-Work/scratch/`. `sheet` writes `-01`, `-02`… files when there are more than 36 thumbnails.

**Thresholds by viewer experience.** They're defaults; the brief can override them.

| Experience | Hook stills | Body stills | Presenter-only run | New elements |
| --- | --- | --- | --- | --- |
| learn fast / quick guide | none > 2 s | none > 4 s unless a reading hold | ≤ 12 s | ≥ 3 per 10 s |
| explain in depth | none > 3 s | none > 6 s unless a reading hold | ≤ 20 s | ≥ 2 per 10 s |
| hang out / story | none > 4 s | judged by eye | ≤ 30 s | ≥ 1 per 10 s |

## The pass (in order; skip what doesn't exist yet)

1. **Hook:** run the check in `video-intro`.
2. **Structure** (`Workflow/Tactics/picks/long-structure.md`, plus the brief's chosen tactics):
   - Write "if you leave now, you miss…" for each chapter and about every 60 s. Flag every gap where it can't be written.
   - Build the open-loop table (opened → mentioned again → resolved) and flag unresolved loops.
   - Look for:
     - a pain point at each section start;
     - visible progression, or the section map at chapter boundaries;
     - breaks in explanations over ~60 s;
     - a relatable variant after out-of-reach examples;
     - compressed waits that state the real duration.
3. **Screen accuracy** (easy to miss, and the worst to ship): read every UI screen and card at full size (`study.py frames`). Look for:
   - test data and placeholders (e.g. "dsadas");
   - garbled characters;
   - counts or claims on screen that contradict the narration;
   - private data.
4. **Visuals and editing:**
   - `study.py analyze <render> <out.json>`: still stretches against the thresholds, and the new-element estimate. The estimate indicates density and undercounts small text, so don't read it as a count.
   - **With a presenter window or inset on screen, also measure the content alone** with `analyze --crop W:H:X:Y` on the content window. For example, `--crop 1390:820:105:195` measures a 1390×820 window whose top-left corner is at (105, 195). A talking inset makes every frame look like it's moving, so the full-frame still share understates how still the content is.
   - **Presenter runs,** read from the 2 s sheet:
     - *presenter-only*: the face and nothing else that informs;
     - *presenter-led*: the face plus cards or text.

     Compare the presenter-only runs with the thresholds.
   - **Eye trace:** check that the viewer's point of focus stays in place across every hard cut. For eased layout moves, sample the moves at section boundaries and those that move the focus to new content, with 0.1 s sheets around them.
   - A focal point on every held screenshot.
   - Captions of ≤ 3 words.
   - Every number on screen with its source.
5. **Sound:**
   - `python3 Workflow/Tools/study/study.py pauses <render> <out.json>`: speech rate, pause share, and whether the planned holds exist.
   - Music switches landing on content shifts.
   - An SFX for each graphic event (from the cue list), with no identical repeats.
   - Every riser followed by a payoff.
   - The feeling needs ears: infer it from the cue list and loudness, and ask the user to confirm.
6. **Ending:** at most one sentence of offer mid-video; subscribe asks tied to a planned video; the end-screen line says why the next video follows.
7. **Packaging promise:** every promise in `BRIEF.md` → "Packaging" is paid off, and early.

## Tightening spoken material: check what the cut removes

When a suggestion removes speech (a repeat, a slow restatement, a false start), first confirm nothing unique goes with it:
1. Build a case with the removed range(s) and the retained alternative(s), in **original recording seconds**. Map render time to source time through the edit's timeline and source mapping (e.g. `edit/timeline*.json`, including any later frame shifts). After close-out the raw recordings are in `12-Archive`, so extract only the needed files.
2. Transcribe both sides (`study.py transcribe`), compare the removed and retained ranges yourself, and list anything unique the cut removes: a fact, a number, a caveat, a name, a joke that pays off later.

Quote that list with the suggestion and let the user decide. Never cut automatically.

## Output

Save the review in `Videos/<video>/11-Work/reviews/<YYYY-MM-DD>-retention-review.md` and summarise it in chat:
- **What already works** (2–5 lines, with the tactic each shows).
- **Numbered suggestions,** most impactful first. Each has:
  - where (timestamp or section);
  - the change;
  - its tactic (`retention/<slug>`, so the user can open the card);
  - the evidence (a measurement, a transcript line or a frame);
  - the effort, including any re-render cost for a finished video.
- **Numbers**, each with its definition:
  - still share (full frame and content only) and the longest still stretch;
  - the longest presenter-only and presenter-led runs;
  - wpm and pause share;
  - first promise word, complete promise, and first proof.

  Add a line of measurement caveats.

The user picks; picked items go to the edit and to `RECORD.md`.

## Notes

- Measurements describe; they don't judge. Hard-cut counts miss animated change, so read the still stretches and the new-element estimate together.
