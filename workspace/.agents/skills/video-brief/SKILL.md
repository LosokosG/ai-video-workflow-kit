---
name: video-brief
description: Use when the user has an idea for a new video, wants to plan or talk through a video, brings new raw footage for a new video, or asks how to make an upcoming video as good as possible. It replaces the hyperframes skill's intent interview for planning. Long-form only; for Shorts, TikTok or Reels use the short-* skills.
---

# Planning a video with the user

Goal: agree the best approach for *this* video with the user, using everything we know, then set up its folder. Every video can look different; past videos are references, not templates.

## The chain

`video-ideas` → **`video-brief`** (with `video-packaging` Draft mode and `video-intro` Plan for the chosen direction) → recording → `youtube-editing-workflow` → `retention-review` → `video-packaging` Final mode → `video-closeout` → `video-performance` once the video is public.

## Before the first question

1. **`Workflow/CHANNEL.md`:** which channel the video is for and its audience.
   - If the profile is blank, infer the audience from what the user says, mark it **proposed**, and ask in the first question round.
   - Client videos use the client's audience and goal.
2. **The last video with published numbers on the same channel:** its `RECORD.md` → "To test next video", and `CHANNEL.md` → "Audience notes". Fold those predictions into the plan.
3. **`Workflow/STYLE.md`, the headings of `Workflow/LESSONS.md`, `Workflow/Tactics/INDEX.md`** (reference cards) and **`Workflow/COMPONENTS.md`**.
4. **Footage,** if any: probe it (format, length, real frame rate), and skim a few frames and the transcript.

No idea yet, or several to choose between? Start with `video-ideas`.

If the idea arrives directly, without `video-ideas`, run its quick checks and fill "Idea origin":
- the originality search (`outliers.py exists`);
- the premise score;
- what really happened, and what proof exists.

## The conversation

1. **Ask at most three questions at a time**, only ones whose answers change the video:
   - who it's for, and the one takeaway;
   - how it should feel (in the user's words);
   - what footage or assets exist or could still be made.

   Skip anything you can infer. Also ask in the first round when it applies:
   - the undecided greeting/name-card choice (`video-intro` → Notes);
   - rights to reused client material.
2. **Propose 2–3 clearly different directions.** Each gets:
   - a structure and a look (background, framing, colour reference, graphics);
   - a one-line sound palette;
   - a **one-line package** (title and thumbnail idea);
   - the proof shot and the first sentence;
   - a rough effort, and why it fits;
   - the key **tactics** that fit this video's viewer experience. Start from the core checks in `Workflow/Tactics/INDEX.md`, then load only the stage lists you need (`Tactics/picks/long-<stage>.md`) or search (`python3 Workflow/Tools/tactics/tactics.py find --format long --stage <stage> --text …`); the chosen ones become the brief's shortlist, one line each on where they land.

   Draw on reference cards and lessons, and say which. Recommend one.
3. **Ask for what would make it better.** List each item and why. For example:
   - the **hook takes** (`video-intro` → Plan);
   - **presenter stills** for the thumbnail, shot in the same session and light;
   - 10 s of the empty green screen (cleaner key);
   - a light behind you (hair separation that grading can't fake);
   - the logo as SVG;
   - the MP4 of a reference video.

   Be specific and proactive.
4. **Let the user choose or mix.** Then, for the chosen direction only:
   - the full `video-packaging` Draft mode (3 packages sharing one core promise);
   - the `video-intro` Plan;
   - **the music:** a free/CC-BY track with provenance, its 2–4 mood shifts marked against the sections, the lift on the key turn, and the drops under takeaways. Prefer tracks with stems; otherwise they can be split locally (`Workflow/Tools/stems/`). Never retime speech to fit the music.
   - **the 3–6 planned holds:** reveals, section ends, the key takeaway.

## Set up

- **Create the folder:** `cp -r _Video-Template Videos/<YYYY-MM-DD-short-title>`. It arrives with the template's folders, `BRIEF.md` and `RECORD.md`.
- **Reusing material from a closed video:** extract only the needed files from its `12-Archive/*.7z` (`7z x … <file names>`), verify their hashes, and hardlink them into the new video rather than copying. Note in both records that the files are shared.
- **Fill every section of `BRIEF.md`,** quoting the user's words where they set direction. The planned holds go under "Structure". It's the video's creative brief; the hyperframes skill's own intent interview is skipped once it exists.
- **Point `Workflow/CURRENT-EDIT.md`** at the new video (a few lines).
- Editing continues with `youtube-editing-workflow`; presenter/green-screen work also uses `presenter-finishing`.
