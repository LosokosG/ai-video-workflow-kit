---
name: presenter-finishing
description: Use when a video has a presenter or green-screen footage to key, needs HDR/HLG colour or alpha handling, frame-timing (PTS) matching, HyperFrames HDR rendering, voice/music/SFX finishing or delivery checks.
---

# Presenter finishing

The slow technical stages of a presenter video, in order. Work only on the stage you're on, and read the matching entries in `Workflow/LESSONS.md` first. Settings from an earlier video are defaults **for the context they came from** (camera and format, green screen and light, keyer, mic and room); probe new footage and calibrate on a 5–10 s moving sample before reusing them.

0. **Probe:** resolution, transfer, primaries, bit depth (`ffprobe -show_streams`), and the **real frame timing** from every frame's PTS, not the fps tag. Note the audio noise floor in pauses before deciding on any repair. Agree the delivery profile with the user; by default it keeps the source resolution, cadence and colour.
1. **Key:** calibrate on a short moving sample (hair, hands, edges) at the delivery size. Ask for 5–10 s of the empty screen if there isn't a clean plate. Use whichever keyer the user has; record its settings in the video's `RECORD.md`.
2. **Integrate:** build every intermediate from measured times, and write down each intermediate's transfer, primaries and alpha type (straight or premultiplied). Convert once, in one place, and verify with a round-trip sample.
3. **Colour:** settle the key first, then agree a reference, then offer three clearly different looks on the same short sample. No grade is a house default; the look is chosen per video.
4. **Render:** use the hyperframes skills' current CLI unless the project pins a version. Check HDR/HLG colour and window edges in motion, at full size, over dark and light backgrounds.
5. **Sound:** measure before processing; process the voice gently and A/B it voice-only at matched loudness. Keep music and effects audible under the voice and check on small speakers.
6. **Deliver:** decode the actual output and check motion, joins, sync, loudness and colour. Label proxies; never pass a proxy off as a final.

Record what you learn: rules in `Workflow/LESSONS.md` (`video-lessons`), one-video facts in the video's `RECORD.md`.
