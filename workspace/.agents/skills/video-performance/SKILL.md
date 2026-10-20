---
name: video-performance
description: Use when the user shares YouTube Studio numbers or screenshots for a published video (audience retention graph, CTR, impressions, views, average view duration, test & compare result), asks how a video performed, or asks what to learn from a video's analytics. Long-form only; for Shorts, TikTok or Reels use the short-* skills.
---

# Learning from a published video

Our own numbers turn borrowed tactics into proven know-how. Only the user can see YouTube Studio: ask, never guess. Say what the numbers show plainly, and label every explanation by how well it's supported.

## 0. Find or open the record

- The video's folder is usually `Videos/<video>/`. If the video was made elsewhere, or has no folder, open a record-only folder `Videos/<publish-date>-<slug>/` with just `RECORD.md` (template) and say so in it.
- Save the user's screenshots and exports in `Videos/<video>/08-Analysis/studio/<YYYY-MM-DD>-d<N>/`, where N is days since publishing.
- **The final-timeline transcript and chapters:** use the one kept at close-out (`05-Exports/Final/`). If there isn't one, get it with `python3 Workflow/Tools/study/study.py fetch <URL> Videos/<video>/08-Analysis/youtube/`, or transcribe the final file.
- Put the status line of `RECORD.md` as `published <date> · <URL>`.

## 1. Ask for (at about day 7 and day 28; at most three asks per message)

- **The link,** the publish date, and whether it was promoted anywhere (where, and when).
- **The video's own Analytics → Engagement:** the audience-retention graph with its **Key moments** panel (Intro, Top moments, Spikes, Dips, Continuous decline), with the exact % around each. Also Studio's comparison with similar-length videos, and the new-vs-returning split.
- **Reach:** impressions, CTR, views from impressions, and traffic sources (with CTR per source if shown).
- **Test & compare**, if a test ran: the result label (Winner / Performed same / Inconclusive), the number of variants, every watch-time share, every image, and the test dates.
- Subscribers gained, comments near the dips, and the user's goal for this video (and `CHANNEL.md` → success measure).

## 2. Read it in three tiers

- **Measured** (state it plainly): e.g. "42 % were gone by 0:30", "views from impressions ≈ impressions × CTR, so ~40 % came from elsewhere".
- **Diagnosed** (a cause checked in *this* video): look at the frames and the transcript at the timestamp before naming a cause. YouTube's meanings:
  - a **spike** is viewers rewatching or sharing that part, or finding it unclear;
  - a **dip** is viewers skipping or leaving.

  Compare the start (0–30 s) with the hook plan in `BRIEF.md` and the numbers in the review notes (`11-Work/reviews/`). Until checked, a cause is a **hypothesis**.
- **Generalised** (changes a tactic's status): only with repeats across videos, or a clean test.

**Evidence rules:**
- A test & compare compares whole packages. Credit a single tactic only if the variants differ in that tactic alone; otherwise record the result against the whole package.
- The label matters: "Performed same" and "Inconclusive" prove nothing. A 41 % share is a lead among three variants but a loss between two.
- During a test, overall CTR and retention blend all the variants.
- Compare CTR by traffic source, and average % viewed only across similar lengths. Always tag d7 or d28. YouTube says numbers under a week old or under 100 views vary more.
- A first video's audience is mostly the creator's own promotion. Note the share of views from outside impressions.

## 3. Record, and route each learning to its one home

- **`RECORD.md`:** the numbers row (template table), the reading with its tiers, and **"To test next video"**: each hypothesis turned into a prediction for the next brief (`video-brief` reads it).
- **Tactic "Used in"** (`Workflow/Tactics/<library>/<slug>/TACTIC.md`): `publish date · video · where · d7/d28 result · tier`. Append a line per reading.
- **Status:**
  - `candidate` → `used` happens at close-out; losing test variants count as used.
  - `proven` needs support in 2–3 videos, or a clean test winner isolating that tactic, or the user's verdict. Show the user the evidence strength with any verdict.
  - `dropped (reason)` after repeated poor results, or when the user says so.

  Then run `python3 Workflow/Tools/tactics/build_index.py`.
- **Audience insights** (where viewers come from, what they rewatch, where they leave) go in `Workflow/CHANNEL.md` → "Audience notes"; the per-video numbers go in → "Results".
- **Workflow rules** that would change how we make videos go to `video-lessons` as proposals. Taste goes into `STYLE.md` only when the user states it.

## Reply shape

1. What the numbers say (measured, 3–5 lines).
2. What it might mean (hypotheses, the most checkable first, each with the check).
3. What we can't say yet, and why.
4. What the next video should test.
5. At most three asks.
