# Rebuild cut-down shorts from layers

`shorts` · formats: short · mode: cut · stages: editing · status: candidate · source: author-experience

**Pick:** Build a vertical short from the long video's layers, never as a crop of the 16:9 master

**What:** A short cut from a long video is rebuilt in a new 1080×1920 project from the long video's source layers: the keyed presenter, the screen recordings, the scene HTML.

**Why it works:** A 9:16 crop of a 16:9 master throws away most of the frame and makes on-screen UI unreadable. A crop of a 1080p key is only about 608 px wide, which looks soft at 1080×1920.

**How we apply it:** `short-edit` → Material: re-lay the scenes for vertical, and re-key the presenter from the original footage when it's shown large. Plan for it at recording time ([`Recording-Prep.md`](../../../Pipelines/Recording-Prep.md) → section 1).

**Use when / skip when:** Every short cut from a long video. Skip it only when the long video was framed for vertical from the start.

**Check:** The presenter and the UI stay sharp at 1080×1920, and no element is a crop of the rendered master.

**Source:** The kit author's own short-form edits.

## Used in

(date · video · where · result)
