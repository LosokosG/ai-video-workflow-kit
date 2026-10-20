---
name: video-packaging
description: Use when writing or improving a video's title or thumbnail (its YouTube packaging), choosing between title/thumbnail options, making thumbnail variants for YouTube's test & compare, or checking whether an idea can be packaged clickably. Long-form only; for Shorts, TikTok or Reels use the short-* skills.
---

# Titles and thumbnails

The package decides whether anyone starts the video. Tactics: `Workflow/Tactics/picks/long-title.md` (the roles column tells checks from angles; `titles-thumbnails/show-the-real-result` always applies). Open each tactic's `TACTIC.md` before drafting; its examples are reference points, not templates.

## Draft mode (idea and brief stage)

Run it for the direction the user chose in `video-brief`. Before that choice, each direction gets only a one-line package, and `video-ideas` uses a 1-line sketch.

0. **Establish what really happened and what proof exists:** recordings, logs, the result itself, and whether it was real data or a test. Also: is the presenter on camera, with their face on thumbnails (`CHANNEL.md` → presenter)? The package may only promise what the video can show.
1. **Name the one or two most intriguing things** the video really delivers, and the viewer motivation it serves (from `Workflow/Ideas.md` / `CHANNEL.md`). If both are empty, ask one question and mark the answer as an assumption.
2. **Find 3+ outlier references** for the angle: `python3 Workflow/Tools/ideas/outliers.py search "<angle phrase>" --n 20 --max-channels 15 --out Workflow/Ideas-Research/<date>-<topic>.md` (created on first use). Note what their packages do; don't copy them. (Fallback: `video-ideas` → Notes.)
3. **Draft 3 packages that share one core promise,** each built on a different main tactic. There's only one intro, and it must pay off every variant. Each has:
   - the title;
   - the thumbnail text (0–4 words that add to the title, never repeat it);
   - a one-line thumbnail picture (hero element, face/expression, background);
   - its tactic slugs (2–4).

   For each title, hunt the key word: list 5–10 options and keep the most concrete. Show the user the winner and at most two rejects, one line each. Search-driven how-tos keep the query words in the title.
4. **Must-pass for every draft:**
   - **Clear, not predictable:** a newcomer knows what it's about, not what happens.
   - **One-second read:** ≤ 3 focal elements.
   - **Works without the title:** it makes sense with the title hidden.
5. Write the drafts into `BRIEF.md` → "Packaging", with each variant's **hero asset** (what must be recorded or made for it). The promise→second table lives in "Hook" → Expectations (`video-intro`); don't duplicate it here.

## Final mode (after the edit, before publishing)

1. **Assets:**
   - **Presenter stills** from `Shared-Assets/Presenter-Stills/` (expression in the file name). If the kit doesn't exist yet, ask the user to shoot it once:
     - 10–12 expressions (shocked, sceptical, amazed, worried, laughing, thinking, confident, "no way", pointing left/right, looking at a laptop);
     - each to the lens and to either side;
     - on the green screen with the video's key light, 12 MP+ or 4K at a fast shutter;
     - plus a few seconds of the empty green screen.
   - The real tool output at full resolution: result screenshots, the finished app.
2. **Build** each variant as a designed composite: a keyed presenter cut-out (from whichever keyer gives the cleanest hair edges) plus the real result, the text and one accent.
   - Use brand tokens once chosen (`Shared-Assets/Brand/README.md`), and the video's palette and type.
   - Tools: a HyperFrames composition at 3840×2160 exported as a still with the snapshot command, or PIL/ImageMagick, with GIMP for retouching. Use the hyperframes skills' current CLI (`npx hyperframes snapshot --help` for the flags), or the version the project pins.
   - Verify this route on the first real thumbnail and record it in `COMPONENTS.md`.
3. **Check sheet:** `python3 Workflow/Tools/packaging/feedcheck.py <variants…> --title "<title 1>" --title "<title 2>" … --ref-search "<niche query>" --out Videos/<video>/11-Work/packaging/` (one `--title` per variant). It shows:
   - a mock desktop and mobile feed among current niche thumbnails;
   - greyscale;
   - no-title and tiny sizes;
   - proxy numbers.

   Check that the candidate is where the eye lands first in the feed, and that its subject still separates from the background in greyscale; then show the sheet to the user.
4. **Variants for YouTube's test & compare:** three packages sharing one core promise, each on a different main tactic (e.g. reaction face / result shot / mistake). Watch time decides the winner, so the video must deliver what each package promises. If the final package differs from the brief's drafts, rerun `video-intro`'s Expectations ticks.
5. **Export:**
   - 16:9 JPG or PNG at 3840×2160, plus a ≤ 2 MB JPG. YouTube Help has listed up to 2 MB from mobile and 50 MB from desktop; re-check the current limit at upload.
   - Put them in `Videos/<video>/06-Publishing/` with the titles in `06-Publishing/titles.txt`.
   - The user uploads; assistants never do.
6. **Record** in `RECORD.md` → "Tactics used and results": the final package, the variants and their tactics, and the test result when the user reports it (`video-performance`).

## Rules

- Stage the composition, never the result: every result a thumbnail shows must be in the video. No manufactured danger or secrets.
- Use other brands' logos or faces only when the video is really about them, and never implying endorsement.
- One accent colour and one focal point. A permanent shock face isn't a style; test calmer variants.
