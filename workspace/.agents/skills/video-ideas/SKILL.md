---
name: video-ideas
description: Use when the user wants video ideas for the channel, wants to brainstorm or research what to make next, has several ideas and must choose one, or asks whether an idea is worth making. Long-form only; for Shorts, TikTok or Reels use the short-* skills.
---

# Finding and vetting video ideas

Goal: a few ideas with real pull for the channel's audience, each able to carry a clickable, honest title and thumbnail. Idea tactics live in `Workflow/Tactics/ideas/` (the Idea group in `Workflow/Tactics/INDEX.md`); open a tactic's `TACTIC.md` when you use it. Any examples inside tactic files illustrate the tactic. They aren't idea suggestions: ideas come from the research and from what the user has actually done.

## First reply: ideas in the same turn

Don't answer only with questions, and don't make the user wait for the full research.

1. Read `Workflow/CHANNEL.md`, `Workflow/Ideas.md` (backlog, problem log) and `Workflow/STYLE.md`.
2. **Blank channel profile?** Infer the niche and the viewer from what the user says, e.g. the channels they name. Write them into `CHANNEL.md` as **proposed**, to be confirmed. The full profile is a planned session with the user; this doesn't replace it. For a client video, the client's audience and goal apply instead.
3. **Quick research** (a few requests):
   - the named channels' recent outliers: `python3 Workflow/Tools/ideas/outliers.py channels <channels…> --out Workflow/Ideas-Research/<date>-<topic>.md` (the folder is created on first use);
   - an originality search for the strongest candidates: `outliers.py exists "<title>"…`.
4. **Reply with 5–8 ideas,** labelled by how researched they are. For each:
   - one line on the idea;
   - the viewer motivation it serves;
   - its premise score (below);
   - its area: broad vs. narrow.

   Recommend one and say why.
5. **Ask at most three questions**, choosing the ones that change the ideas most:
   - which viewer (e.g. beginners vs. experts);
   - **what the user has actually done, tried, or could film** (real stories beat invented ones and can't be copied);
   - whether they'll be on camera, with their face on thumbnails.
6. **Save** the ideas in `Ideas.md` with today's date; `status: raw`.

## Deeper research (when the user wants it, or before committing to a series)

1. **Audience watch list:** the channels the target viewer already watches.
   - Use the channels the user names plus similar ones; for fast-moving topics, the latest 6–12 months of uploads, not all-time Popular.
   - Ask for YouTube Studio → Analytics → Audience screenshots only once the channel has an audience; a new channel's panels are empty.
2. **Patterns and the research checklist:** 2–4 "our audience wants…" statements with example videos, and the checklist in `Ideas.md`.
3. **Generate:**
   - combinations of two things the audience already likes;
   - concepts that worked for a neighbouring audience, found with `outliers.py search`: write many phrases for what the viewer wants, but search only the best 3–5;
   - every transferred concept must fit the channel and the viewer;
   - save concepts with a note and tags.

   For a new channel, outliers from small and mid channels (roughly 10k–100k subscribers) are the best evidence. A huge channel's outlier often rides on its audience.
4. **Problem log:** real problems the user hits while testing tools go in `Ideas.md` → Problem log. They're candidate videos (`ideas/problem-log`).

## Premise score

Count the retention tactics already inside the idea: goal, obstacle, stakes, time limit, competition, progression, surprise. A plain how-to scores on pain point plus progression, which is fine. Invented drama doesn't count.

## Vet before committing, in this order

1. **Fresh perspective:** the user re-reads the ideas ≥ 2 days later. If the user picks one sooner, go ahead and record "fresh look skipped by the user". Don't block them.
2. **Original:** usually already done in the first reply; otherwise run `outliers.py exists`. If it exists, find a better package or a twist.
3. **Best option:** show the survivors side by side with the evidence (outlier references, area, premise score). The user chooses.
4. **Title and thumbnail first:** write motivation → value → a 1-line package sketch. A clear sketch is enough here; the full three drafts come in `video-packaging` after the brief starts. No clear package means drop or re-angle the idea.

## Where things go

- **`Workflow/Ideas.md`:** curated research summaries, the problem log, and one entry per idea (format in the file).
- **`Workflow/Ideas-Research/<date>-<topic>.md`:** raw tool output, dated (create the folder if needed).
- **The chosen idea** goes to `video-brief`. Its research summary, premise score, fresh-look status and the proof that exists go into `BRIEF.md` → "Idea origin".

## Notes

- If `outliers.py` is missing or fails, use yt-dlp directly: `yt-dlp --flat-playlist --print "%(view_count)s\t%(channel)s\t%(title)s" "ytsearch15:<query>"`, or a channel's `/videos` URL with `--playlist-end 60`.
- Keep YouTube requests modest; the tool caches channel medians. Outlier scores are evidence, not predictions; on tiny channels they mostly reflect promotion.
- Never reuse other creators' titles or thumbnails verbatim; keep the transposition.
