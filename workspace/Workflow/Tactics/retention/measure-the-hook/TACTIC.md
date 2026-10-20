# Measure the hook before every review render

`retention` · core: yes · stages: hook · status: candidate · source: author-experience

**Pick:** Measure the first 30 s (first word, promise, proof, stills) before showing a cut

**What:** Before a review render goes to the user, measure its first 30 seconds with the study tools instead of judging them by feel.

**Why it works:** An intro that feels fine in the timeline can still open on a greeting, hold a still frame for five seconds or show the proof late. The numbers catch it before a viewer does.

**How we apply it:** The hook check in `video-intro`: `study.py transcribe --words` for the first word and the promise times, `analyze` for still stretches and new elements (with `--crop` when a presenter inset is on screen), `pauses` for the speech rate, and a contact sheet read together with the transcript. The result goes in `11-Work/reviews/<date>-hook-check.md`.

**Use when / skip when:** Every long video. Skip it for a probe nobody else will see.

**Check:** The review note lists the first word and its time, the complete-promise time, the first proof, and every still stretch over ~4 s.

**Related:** [`titles-thumbnails/show-the-real-result`](../../titles-thumbnails/show-the-real-result/TACTIC.md)

**Source:** The kit author's own review routine (`video-intro` → Hook check).

## Used in

(date · video · where · result)
