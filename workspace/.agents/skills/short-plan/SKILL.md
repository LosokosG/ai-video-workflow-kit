---
name: short-plan
description: Use when the user wants ideas for Shorts, TikToks or Reels, wants to plan, script or hook a short-form video, or asks which shorts to cut from one of our long videos.
---

# Planning a short

Short-form only: load the core checks in `Workflow/Tactics/SHORTS-INDEX.md`, not the long-form library or skills. Search the short-form tactics with `python3 Workflow/Tools/tactics/tactics.py find --format short --stage <stage> [--face presenter|faceless|mixed] [--mode native|cut]` and open one with `tactics.py show <slug>`. The tactics picked go into `SHORT.md` → Tactics, and later steps read that shortlist. Take long-form knowledge only when it genuinely helps this short (`STYLE.md`). Short-form preferences are in `STYLE.md` → "Short-form"; the platforms are YouTube Shorts, TikTok and Instagram Reels, from one master.

## Before starting

Read `Workflow/CHANNEL.md` → "Shorts" (if it's empty, ask what the shorts are for and who they're for, and write the answer there) and `Videos/Shorts/RESULTS.md` (what has worked so far).

**Whose channel?** A short goes where its long video lives. Shorts cut from a client's video go on the client's accounts, never on the user's own channel, and stay out of the own channel's results comparison. Write it in `SHORT.md` → Channel/account; if nobody has said where the client's long video is published, ask.

Short ideas that aren't picked yet go in `Videos/Shorts/IDEAS.md` (the long-form `Workflow/Ideas.md` is for long videos). A short in progress gets one line in `Workflow/CURRENT-EDIT.md`.

## Native short

1. **Ideas:** propose 5–8 ideas. Each gets its face mode (presenter, faceless or mixed; the user decides per short), the payoff, and one hook line. Recommend one. Ask at most three questions, e.g. what the user has actually done or can film.
2. **Hook:** start from the payoff and write three to five hook lines that open on it from different angles. Plan what the first second shows, the on-screen text (burned in by default) and the first sound, not only the words. The user picks.
3. **Beats:** the hook, the value, and the payoff, with target times for the planned length. Pick the tactics with `tactics.py find` (filtered by this short's face mode and mode).
4. **Script and shot list** in `script.md` next to `SHORT.md`: talking points rather than a word-for-word script, except for the hook and the last line. Recording prep for the user: `Workflow/Pipelines/Recording-Prep.md`.
5. **Set up** `Videos/Shorts/<YYYY-MM-DD>-<slug>/` from the workspace root's `_Short-Template/`, and fill `SHORT.md` → Plan.

## Shorts cut from a long video

1. **Read the long video's reviews first** (`11-Work/reviews/`): known on-screen defects and private data to avoid.
2. **Score transcript windows** from the long video's word-timed transcript (a hand-corrected word file beats whisper for names) and `RECORD.md`; without a transcript, make one with `python3 Workflow/Tools/study/study.py transcribe <media> <out> --words`. For each candidate window, note whether it stands alone, whether its payoff is inside the window, and how much context a stranger would need. Save the candidate list in `Videos/Shorts/` (closed videos are read-only).
3. **Check the top 3–5 at frame level:** private data, readable UI, keyed edges.
4. **The user picks.** Each pick gets its own `Videos/Shorts/<date>-<slug>/` with `Mode: cut from …` and the source ranges. Note the short in the long video's `RECORD.md`.
5. **Plan a new hook line or a re-order** when the passage's first line doesn't hook.

If the long video is closed out, its raw originals are in `12-Archive/*.7z` (extract only what's needed). A presenter shown larger than in the long video needs a re-key from the original footage at that size.

## Rules

- Stage the composition, never the result: every result shown must be real. The same goes for challenges, stakes and reactions.
- Never reuse other creators' footage, lines or branding.
- Platform facts change. Re-check any limit or setting against the platform's current help pages before relying on it, and write the date you checked next to it.

Next: `short-edit`.
