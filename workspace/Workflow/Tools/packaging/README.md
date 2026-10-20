# Thumbnail feed check (`feedcheck.py`)

Makes one PNG **check sheet** per candidate thumbnail, so it's judged the way viewers meet it: among current niche thumbnails at real size, never alone on a canvas. Used by the `video-packaging` skill. PIL + stdlib; yt-dlp only to fetch reference titles and thumbnails, never videos.

```bash
python3 Workflow/Tools/packaging/feedcheck.py A.png B.png C.jpg \
    --title "The video title" --ref-search "claude code tutorial" --out Videos/<video>/11-Work/packaging/
# one --title per candidate if they differ; --refs DIR instead of --ref-search; --position 1–12, --seed,
# --channel NAME, --meta "1K views • 1 day ago", --duration 12:34, --refresh
```

**Each sheet has:**
- **(a) A mock desktop home feed.** It's YouTube's dark theme at real size: 4 columns of 360×202 tiles, each with a two-line ellipsised title, channel and views. The candidate sits among up to 11 references, in the same random slot on every sheet of a run.
- **(b) The same feed in greyscale.**
- **(c) A mobile feed** at 390 px wide, and the watch-page sidebar size (168×94).
- **(d) The candidate alone** at 320×180 with no title, in greyscale and at 160×90.
- **(e) Three proxy numbers** beside the references' median and range: centre-vs-border lightness contrast, Hasler–Süsstrunk colourfulness and edge density. There are also upload checks (16:9, at least 640 px wide, under 2 MB for mobile).

With two or more candidates, `feedcheck-compare.png` shows them side by side at 320×180.

`--ref-search` saves the titles and thumbnails in `ref-cache/<query-slug>/` (`refs.json` plus `<id>.jpg`) with one yt-dlp call, and reuses them for 7 days. Those are other creators' thumbnails, for internal reference only. `--refresh` doesn't remove old images; trash the folder when it's no longer needed.

**Limits.**
- **It's a mock, not YouTube's UI.**
  - Noto Sans stands in for Roboto; install Roboto and it's picked up.
  - Spacing is approximated, and avatars are coloured initials.
  - There are no hover previews, "New" badges or light theme.
  - Emoji in titles are dropped.
- **Size is in CSS pixels.** On a 2× display, view the sheet at 200 %.
- **References are logged-out search results,** not a viewer's personalised home feed.
- **The numbers are prompts for the eye, not verdicts.**
  - Centre-vs-border assumes a centred subject, and letterbox bars count as border.
  - Colourfulness can't tell one accent from a rainbow.
  - Edge density at 320×180 barely counts faint detail. A deliberately busy low-contrast test scored 15.9 %, against 9.1 % for a clean one and 15–51 % for real niche thumbnails, which are full of faces and text.
  - Compare against the references, not an absolute bar.
