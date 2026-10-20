# Reusable scene index

Scene treatments with real code that a new video can adapt. All are **candidates** unless marked approved; approval is recorded per video. Copy the source into the new video's `10-Project/` and change content, anchors and colours there; don't edit the originals. Add an entry when a treatment is actually implemented, and mark it approved only with the user's approval.

| Treatment | Source | Status | Reuse / change |
| --- | --- | --- | --- |
| (none yet) | | | |

## Ideas to build on a first video that needs them

Build each on the first video that needs it, as 3 variants on a real 10 s beat; the user picks, then add the chosen one to the table above.

| Treatment | What it should do |
| --- | --- |
| Focus treatments | On a real screenshot or screen recording: spotlight (dim/blur outside a region), animated highlighter stroke on key text, draw-on underline/circle/arrow, soft glow; each anchored to the spoken word, in brand colours |
| Section map | One graphic that previews the sections in the hook (later labels hidden or blurred) and returns at each chapter boundary with the current item lit and finished items marked; chapter names match the YouTube description chapters |
| Caption chunking | Word-linked captions re-chunked to 1–3 words per screen |
| Recorded-page pan + guided pointer | A page atlas from real recorded states, eased pans, one simulated pointer with click pulses; never bake a recorded cursor into a scrolling page |

Layering rule (HyperFrames): position sub-composition hosts by id/class, never by `[data-composition-src]` (the render compiler removes that attribute). Check new aspect ratios, timings or palettes before reusing a verified profile. Brand choices: `../Shared-Assets/Brand/README.md` and `STYLE.md`.
