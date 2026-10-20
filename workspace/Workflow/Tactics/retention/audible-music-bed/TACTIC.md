# Keep music and effects audible under the voice

`retention` · stages: sound · status: candidate · source: author-experience

**Pick:** Carve the music around speech instead of burying it; check on small speakers

**What:** Keep the voice clear by carving the speech band out of the music bed while the presenter talks, not by turning the whole bed down until nobody hears it. Sound effects stay short and present.

**Why it works:** On an earlier video, a bed about 19 LU under the voice left the user unable to hear the music or the effects at all; the sound design was there but did nothing.

**How we apply it:** A dynamic speech-band carve on the bed. A starting point from one long-form setup: music about 12 LU under the voice during speech and about 8 LU under it in pauses; short, restrained hits with a fast decay, never the same effect twice in a row. Measure with `study.py pauses` (the bed level in pauses) and listen on a phone or laptop speaker.

**Use when / skip when:** Long videos with a music bed or effects. The numbers are a starting point: re-measure with a new mic, room or genre. Shorts start quieter (`short-edit` → Sound).

**Check:** `pauses` reports the bed-in-pauses level, and the user confirms they can hear the music and the effects on a small speaker.

**Source:** The kit author's own mixes ([`Workflow/LESSONS.md`](../../../LESSONS.md) → "Music and sound effects must be clearly audible under the voice", "Sound effects need weight without drama").

## Used in

(date · video · where · result)
