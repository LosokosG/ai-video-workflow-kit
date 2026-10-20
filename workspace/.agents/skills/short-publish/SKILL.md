---
name: short-publish
description: Use when a Short, TikTok or Reel is ready to post, when writing its titles, captions, hashtags or cover per platform, when replying to its comments, or when the user shares its numbers or asks how shorts are performing.
---

# Posting a short and learning from it

Short-form only. Assistants never post, upload or reply on the user's accounts. We prepare the package; the user posts.

## Before posting: the gate

On the approved master, check:
- the `short-edit` QC still holds for the exact file being posted;
- the hook, captions and key result sit clear of each target app's overlay;
- nothing private is visible (names, emails, keys, dashboards), frame by frame where UI is on screen;
- every result shown is real and in the short;
- each platform's current limits (length, file size, caption length, hashtags), re-checked on its help pages.

A failed item goes back to `short-edit`.

## The package (`<short>/exports/`)

Drafts written at plan stage are the starting point; set the final text here, after the gate.

- **Files:** one master MP4 and a cover per platform, with its title inside the area the app doesn't crop.
- **Per platform, in `SHORT.md` → Posting package:**
  - title or caption;
  - hashtags within the platform's limit;
  - the cover frame or image;
  - AI disclosure where the content is realistic AI;
  - the link back to the long video (YouTube: "Related video"; elsewhere the caption or pinned comment);
  - brand tags for brands that appear;
  - the music credit wherever a licence requires one (CC-BY: in every caption).
- **Client shorts** go on the client's accounts (the related-video link only works within one channel).
- **Engagement:** draft the pinned comment and the question it asks.

Give the user a short checklist to post from, and note the posting time.

## After posting

Ask the user for the numbers as screenshots from each app's analytics (only they can see them), first after about a day as a technical check, then after about a week for a verdict against the user's own earlier shorts.

Record the results:
- a row per platform in `Videos/Shorts/RESULTS.md`, with the date read;
- the decision in `SHORT.md` (remake, drop or rework);
- each tactic's "Used in" line (`Workflow/Tactics/shorts/<slug>/TACTIC.md`); set `candidate` → `used`, then run `python3 Workflow/Tools/tactics/build_index.py`.

`proven` needs repeats across shorts. One short is an anecdote.

**Comments:** the agent can draft replies from comments the user pastes; the user posts them. Repeated criticism goes to `CHANNEL.md` → "Audience notes" or becomes a lesson via `video-lessons`.

## Rules

- Platform facts change. Re-check a limit or setting if it's older than about 6 months or the app looks different.
- No engagement tricks: no seeded comments, no fake reactions, no re-uploading a flop unchanged.
