---
name: video-study
description: Use when the user shares a YouTube link, a video file (MP4/MOV) or a GitHub repo/skill to learn from — editing or YouTube-craft techniques, AI video workflows, a video they like and want analysed or partly replicated — or asks what our pipeline could adopt from it.
---

# Studying a video or skill

Goal: extract as much usable knowledge as possible and turn it into **specific proposals** for our workflow. The user decides what's adopted; nothing changes on its own.

Tool: `python3 Workflow/Tools/study/study.py` (run without arguments for usage). Study folder: `Workflow/Studies/<YYYY-MM-DD>-<short-slug>/` (create it, and `Workflow/Studies/`, if needed). Downloads go in its `scratch/` subfolder (same drive, so the OS trash works; a temp directory elsewhere can't be trashed).

## Steps

1. **Agree a download cap** in one question: captions and metadata (a few MB) plus clips up to ~N MB. For a GitHub source, the clone. Stay within it.
2. **Read everything that's text:** `study.py fetch URL <study-dir>` writes the description (read it: linked tools and resources matter), chapters, a timestamped transcript, the thumbnail, the most-replayed heatmap peaks and download-size estimates. Read the **whole** transcript. Check `captions.type` in the output: if it's machine-translated, missing or suspect, `transcribe` a short clip and compare.
3. **Outline it:** timestamped sections, every technique or claim, and the **moments that need eyes** (demos, "as you can see", before/after, UI steps, on-screen text, visual style). Most-replayed peaks are strong candidates.
4. **Look only where needed, within the cap:** `study.py segment URL START END <study>/scratch/<name>.mp4` (30–90 s clips; `--audio` for sound). For sound lessons, the whole audio is cheap (~1 MB/min). Then `frames`, `sheet` and `analyze` (add `--fine` for per-second loudness) and `pauses` (speech rate, pauses, bed level). Look at the frames yourself; clip times map back to source time automatically.
5. **Local MP4 from the user:** no download. Run `analyze`, `sheet`, `pauses` and `transcribe` on the whole file, look at frames, and combine it with what the user said about why it's good.
6. **GitHub skill or tool:** clone at a fixed commit into scratch. Read the README/SKILL.md and the code: what it does, what it installs, what it sends where, its licence, and its overlap with our skills and tools. Don't run install scripts or send our media anywhere without the user's OK.
7. **Compare with what we do:** `Workflow/LESSONS.md` headings, `STYLE.md`, any relevant playbook in `Workflow/Pipelines/`, and the last video's actual recipes (e.g. its audio recipe JSON). Measure our own final with the same commands when a number comparison helps.
8. **Write the outputs** (below), add one line to `Workflow/Studies/INDEX.md` (create it if needed), and move the `scratch/` folder to the OS trash (`gio trash` on Linux).
   If the source teaches tactics (finding ideas, titles/thumbnails, retention), capture **every** one separately in `Workflow/Tactics/` (format and rules in its `INDEX.md`), including tactics only shown on screen.
   - Before trashing `scratch/`, put the source's own examples in each tactic's `examples/`: the transcript excerpt, frames of each example, and clips of 20 s or less where motion or sound is the point (`study.py examples` builds them from a spec). They are other people's material, kept for private reference only: `.gitignore` keeps `examples/` folders out of git; never publish them.
   - Check the library for overlaps first. A tactic that already exists gets the new source and prefixed examples added, never a second folder.
   - Then rebuild the pick list: `python3 Workflow/Tools/tactics/build_index.py`.
   - Subagents can't write `.md` files: return each tactic as a block (slug, stages, what, why, how, use/skip, check, source, examples) for the parent to write.
9. **Present the proposals in chat**, numbered, so the user can pick. Adopted ones become candidate lessons (`video-lessons`) or playbook changes.

If you're running as a subagent and can't write report files, return the full text of `FINDINGS.md`, `card.md` and the INDEX line for the parent to save.

## Outputs

`FINDINGS.md`:
```
# <title> — study
Source (link, channel, date, length) · studied <date> · what was read (description, full transcript, caption type) and seen/measured (which ranges, total MB)
## What it teaches      (timestamped points, in our words)
## What we measured     (optional: numbers, method, and the same numbers for our last video)
## Already doing / doing better
## Proposals            (numbered: the change · where in our workflow · why · effort · how to test it on the next video)
## Not worth adopting   (and why)
```
`card.md` (when the video's style or craft is itself the lesson, or the user sent it as a reference): hook (first 10 s), structure and pacing, visuals (layouts, graphics, text density, palette), sound, title and thumbnail, most-replayed moments, what the user said, sampled ranges, 4–8 frames in `frames/`.
Also keep `transcript.txt`, `description.txt`, and any measurement script in `evidence/`.

## Notes

- Say plainly what you watched, heard or only measured. Captions can be wrong. `analyze` numbers describe a video; they don't judge it (hard-cut counts miss animated changes; use `visual_changes` and `still_share` too).
- A local MP4 beats a link when the video is private or unlisted, or when full-length measurements matter (pacing, sound). The link still gives the description, chapters, captions and heatmap. Best for a full style study: both, or the user's OK for a whole download. Ask for the MP4 when it would change the result.
- YouTube may answer 429/403 after many requests. Wait and retry later, or ask the user for the file.
- 720p is enough to read on-screen text and UI (about 3–4 MB/min). Use 1080p only for style or quality studies. A whole download cut into short example clips suits tactic-list videos.
- Auto-captions get names wrong (e.g. "Tubebuddy" for Velio). Check brand and tool names against the screen, the description or a short local transcription. Smaller videos have no most-replayed heatmap.
- Several studies can run in parallel as subagents, one per source. Give each the download cap and the study folder.
- Learn techniques, never reuse their footage, music or branding.
