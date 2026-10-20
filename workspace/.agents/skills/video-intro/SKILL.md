---
name: video-intro
description: Use when planning, scripting, recording or editing a video's intro or hook (roughly the first 30 seconds), when an intro feels slow or loses viewers, or when choosing between hook takes. Long-form only; for Shorts, TikTok or Reels use the short-* skills.
---

# Intros that keep viewers

Most intro drop-off is disappointment: the opening doesn't deliver what the title and thumbnail promised. Hook tactics: `Workflow/Tactics/picks/long-hook.md`; `retention/measure-the-hook` applies to every video. For each tactic you use, read its `TACTIC.md`. The brief's viewer experience and natural pacing (`STYLE.md`) set how fast is right.

## Plan (with the brief, before recording)

**Start from the package.**
- No package draft yet? Run `video-packaging` Draft mode first and use its recommended draft.
- The test & compare variants must share one core promise. The intro pays off that promise and each variant's hero element.

Fill `BRIEF.md` → "Hook":

1. **Expectations:** the single promise→second table. List every title and thumbnail element, including each test variant's hero element, and the feeling the package promises. Next to each, note the second of the intro that pays it off.
2. **The proof shot:** the real result on screen within ~5 s. It can be a new recording, or taken from existing or archived material.
3. **The opener: pick ONE type per variant.** They're alternatives, not a stack:

   | Opener | Use it for |
   | --- | --- |
   | result shown as proof | build stories, demos |
   | the viewer's own question | explainers, reviews (skip it for build stories) |
   | one intriguing detail | case studies, stories |
   | a counterintuitive fact | explainers |
   | introduce → reveal | problem or story openings |
   | the pain first | tutorials |
   | a self-aware interrupt | sceptical audiences |

   Channel videos open without a greeting or preamble unless `STYLE.md` records the user choosing otherwise. Client videos may keep one short introduction line.
4. **Write 3–5 variants**, each checked for:
   - the strongest words;
   - at most 2 promises plus one extra;
   - an outcome line.

   Present them with a recommendation; the user picks. Record the pick and the rejects in the brief.
5. **Two clocks:**
   - the **first promise word** (~2 s for channel videos);
   - the **complete promise** (the full promise plus the outcome line).

   The complete promise comes within ≤ 5 s for a "wow" demo, 10–20 s for a tutorial, and ~15–25 s for a build story or case study, with the proof shown in the first seconds. A story-led explainer can take 20–30 s if every sentence moves it on.
6. **Takes to record:**
   - the chosen variant;
   - the runner-up (a different opener type);
   - the chosen variant again with more energy.

   Shoot the thumbnail stills in the same session (`video-packaging`).

With existing footage, pick among the takes by the same checks. If the best take is weak, ask for a re-recorded hook and say why.

## Edit

- **Open mid-motion:** speech by ~0.7 s and the first graphic by ~1 s. The first sound follows the promised feeling: a hit for "wow", a slow push and one soft sound for calm.
- **The hero asset planned in the package is the first thing on screen.** Make that asset before the hook edit; the final thumbnail is built from it or cut from the hook frame. If only a staged photo is possible, match its palette and type instead.
- **Show while talking.** Use full-frame presenter only for 1–2 confident lines.
- **Change something every 2–4 s,** mostly by animation.
- **Put 2–4 hook keywords on screen as type.**
- **Layer:** 1–2 layers per beat, and the hook's own music cue.
- **For list-shaped videos,** add a blurred preview of the parts or one open loop with a named payoff.

## Hook check (before every review render)

1. Measure the first 30 s of the review render, or a labelled 30 s hook probe if no full render exists yet. From the workspace root, with `S="python3 Workflow/Tools/study/study.py"` and the outputs in `Videos/<video>/11-Work/scratch/`:
   - `$S transcribe <render> hook.txt --start 0 --end 30 --words` gives the words, the first-word time, and word-level times in `hook.words.json` (use them to time the promise words);
   - `$S analyze <render> hook.json --start 0 --end 30` gives still stretches and new-element onsets (add `--fine` for per-second loudness). With a presenter window on screen, run it again with `--crop W:H:X:Y` on the content window;
   - `$S pauses <render> hook-pauses.json --ranges 0-30` gives the speech rate;
   - `$S sheet <render> hook-sheet.jpg 0.5 --start 0 --end 30` makes contact sheets stamped with source times (`hook-sheet-01.jpg`, `-02.jpg`).
2. Read the transcript and the sheet together for what the numbers can't give: the promise and proof times, and presenter full-frame share.
3. Write down:
   - the first word and its time, and that it isn't a greeting;
   - the first promise word and the complete promise against the clocks;
   - the time to first proof;
   - still stretches (none over ~4 s unless deliberate), and new elements per 10 s;
   - every row of the Expectations table ticked with its second;
   - the feeling in one word, which should match the brief.

Save the check in `11-Work/reviews/<YYYY-MM-DD>-hook-check.md`. Failures become `retention-review` suggestions.

When the right density is unclear, offer the user a **bare vs. layered A/B** as two short labelled SDR probes (or a Studio toggle). If `video-packaging` Final mode changes the package, rerun the Expectations ticks.

## Notes

- The greeting/name-card choice for channel videos is **not decided yet**. Ask the user once, then record the answer in `STYLE.md`.
