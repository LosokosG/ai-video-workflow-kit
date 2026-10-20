# Lessons

Short rules learned from real videos. Scan the headings at the start of a task and read the ones that apply. Each lesson has a **scope** (where it applies) and a **status**: `starter default` (learned on the original author's videos and shipped with this kit; keep it, change it or retire it once your own experience says otherwise), `proposed` (drafted from your evidence, not yet confirmed by you), `confirmed` (you agreed), `context default` (true for the named setup, re-check when it changes) or `superseded by …` (kept for rollback). Add or change lessons with the `video-lessons` skill; evidence goes in each entry's **Evidence** line. Deeper how-to lives in playbooks under `Pipelines/`.

## Show a Studio preview or short sample before any full render
- **Context:** any change that needs rendering.
- **Problem:** full renders take hours; the user wants to judge in Studio or on a short clip first.
- **Rule:** iterate in Studio or on short encoded probes; render the full video only when the user asks or has already authorised it.
- **Scope:** all videos · **Status:** starter default

## Do the technical work yourself; stop only for real choices
- **Context:** setup, tool wiring, batch runs, fixes.
- **Problem:** the user had to click through setup steps that an agent can do.
- **Rule:** handle setup and technical steps yourself. Stop only for creative choices, approvals the safety rules require (installs, deletions, uploads) or material only the user can supply.
- **Scope:** all work · **Status:** starter default

## Long jobs get one simple progress view and a clear "you can leave"
- **Context:** renders, key batches, anything over ~10 minutes.
- **Problem:** "is it done?" is the most common message; an elaborate progress page wasn't wanted.
- **Rule:** give one simple progress view (percent + rough ETA), say plainly when the user can walk away and when it's done. Run long renders detached, so they survive the session ending.
- **Scope:** all work · **Status:** starter default

## The user chooses replacement takes from playable side-by-side options
- **Context:** fixing stumbles, repeats or look-aways by swapping in another take.
- **Problem:** text-only take suggestions can't show delivery; swaps change meaning and tone.
- **Rule:** show the current passage and each candidate as playable clips with enough context to judge the join, always including "keep original". Don't install a swap before the user picks. Trims inside the same take don't need this.
- **Scope:** all videos · **Status:** starter default

## Keep natural pacing and every useful explanation
- **Context:** cutting any talking video.
- **Problem:** a forced one-minute cut removed the intro, outro and useful off-script parts and created jumpy cuts.
- **Rule:** no default runtime cap. Keep intros, outros and useful off-script additions. Cut false starts, repeated words, look-aways and dead air *inside* sentences. Keep deliberate pauses between ideas, and anything the user explicitly keeps.
- **Scope:** all videos (a taste default; `STYLE.md` overrides) · **Status:** starter default

## Cut picture and sound together on whole frames
- **Context:** removing a pause or a word.
- **Problem:** audio-only cuts drift out of lip sync; a smooth visual transition doesn't repair an unnatural audio cut.
- **Rule:** remove whole frames of picture and sound together, snap to room tone, and re-map every later cue (captions, SFX, graphics) through the same time map.
- **Scope:** all videos · **Status:** starter default

## Settle the key before grading, and judge both in motion at full size
- **Context:** green-screen videos with a colour look.
- **Problem:** ten colour looks were made before the key was settled and none was picked; small web previews and stills hid edge flicker and spill.
- **Rule:** key first (calibrated on a moving sample), then agree a reference, then make three clearly different looks on the same short sample. Judge at full size, in motion, over dark and light backgrounds.
- **Scope:** all keyed videos · **Status:** starter default

## Measure real frame timing before any keying or retiming
- **Context:** phone footage (and any variable-frame-rate source).
- **Problem:** a nominal "55 fps" hid two 50 fps shots and a timestamp gap; the key batch then repeated/skipped frames, fixed only by per-frame matching afterwards.
- **Rule:** read every frame's PTS from the original first; build intermediates and mappings from measured times, never from the fps tag.
- **Scope:** all videos (check) · **Status:** starter default · **See:** `presenter-finishing` skill, stages 0 and 2

## Write down the colour encoding and alpha type of every intermediate
- **Context:** keys, EXRs, ProRes intermediates, HDR delivery.
- **Problem:** one editor's EXRs held straight alpha with HLG-coded BT.2020 values, not linear light. Treating them as linear or premultiplied causes halos and wrong brightness.
- **Rule:** record transfer, primaries and alpha type next to each intermediate; convert once, in one place, and verify with a round-trip sample.
- **Scope:** all videos (check) · **Status:** starter default

## Key at the delivery size
- **Context:** 4K footage when the user chooses a 1080 delivery (the default delivery keeps the source resolution).
- **Problem:** 4K keys cost roughly four times the time and storage for no visible gain at 1080.
- **Rule:** once the delivery size is chosen, resize (Mitchell) to it before keying; for a 4K master, key at 4K.
- **Scope:** 1080 deliveries · **Status:** starter default

## Resume long batches from checked outputs, not receipts
- **Context:** any resumable batch (keys, renders, extractions).
- **Problem:** "complete" receipts and existing files were trusted without checking the inputs or settings; stale results can be reused under a different configuration.
- **Rule:** skip work only when the inputs and settings match and the actual outputs validate (readable, right count, sane values).
- **Scope:** all pipelines · **Status:** starter default

## A professional voice comes from light, measured processing
- **Context:** narration recorded in one mic and room.
- **Problem:** a "very pro" sound was reached with gentle EQ, de-essing, light compression, take matching and breath reduction; denoise or AI enhancement wasn't justified by the recording.
- **Rule:** measure first, process gently, A/B voice-only at matched loudness. New mic or room: re-measure instead of reusing another setup's EQ numbers.
- **Scope:** the mic and room you measured · **Status:** starter default

## Music and sound effects must be clearly audible under the voice
- **Context:** videos with a music bed and SFX.
- **Problem:** a mix that buried the music (~19 LU under the voice) and the SFX left the user unable to hear them.
- **Rule:** keep the voice clear through a dynamic speech-band carve rather than by burying the bed. A workable starting point was music ~12 LU under the voice in speech and ~8 LU in pauses, with SFX clearly present. Check on small speakers too.
- **Scope:** all videos (the balance numbers are a starting point) · **Status:** starter default

## Sound effects need weight without drama
- **Context:** emphasis cues.
- **Problem:** a long sub-drop impact on a key word felt overly dramatic.
- **Rule:** short, restrained hits with a fast decay; vary SFX so the same sound never repeats back to back.
- **Scope:** all videos · **Status:** starter default

## Screen walkthroughs: the user's own recordings, one smooth guided pointer
- **Context:** showing websites or apps.
- **Problem:** an automated capture looks bad; jumpy recorded cursors and scroll jumps look laggy.
- **Rule:** prefer the user's own screen recordings. Hide the recorded cursor and add one guided pointer with eased movement, click pulses, eased scrolls and short reading holds.
- **Scope:** walkthrough scenes · **Status:** starter default

## Judge the encoded output, not screenshots
- **Context:** any render claim.
- **Problem:** Studio screenshots and still frames can't show motion, HDR, sync or audio joins.
- **Rule:** decode the actual output and check motion, joins, sync, loudness and colour before calling anything done.
- **Scope:** all videos · **Status:** starter default
