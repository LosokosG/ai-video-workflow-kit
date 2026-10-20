# Outlier finder (`outliers.py`)

Scores videos by **views ÷ their channel's median views**, from `yt-dlp --flat-playlist` listings: no login, no downloads, no paid tool. It's the free version of what Velio and vidIQ sell. Used by the `video-ideas` and `video-packaging` skills.

```bash
T=Workflow/Tools/ideas/outliers.py
python3 $T channels @SomeChannel @OtherChannel         # median + top 15 per channel; latest 60 uploads by default
python3 $T channels @SomeChannel --popular             # all-time: every upload (cap 1000), sorted by views
python3 $T channels @SomeChannel --latest 30           # a different window
python3 $T search "claude code workflow" "ai coding tips" --min-views 10000 --min-median 1000
python3 $T exists "How I use Claude Code to edit videos" "Claude Code video editing"
python3 $T search "…" --out Workflow/Ideas-Research/2026-09-28-ai-coding.md   # new dated file instead of stdout
```

- **channels:** the long-form videos tab only (Shorts and live streams are excluded), newest first. It prints the window, the median, the subscriber count and the top 15 by score. With several channels it adds the top 15 by views and by score across all of them. Within one channel, score order and view order are the same.
- **search** (desire-phrase search): `ytsearch20` per phrase, Shorts skipped, then each result's channel median over its latest 30 uploads, ranked by score, with subscribers. At most `--max-channels 15` fresh channel lookups per run, most-viewed results first; the rest are listed as unscored.
- **exists** (originality search): the top 10 results per title and variation, with views, channel, age and a keyword-overlap "match".
- **Flags:** videos under 30 days old are marked **(new)**, since they're still gaining views. Channels with a median under 1,000 get a **tiny median** note: their scores mostly reflect promotion.
- **Output:** markdown on stdout. `--out FILE.md` writes a new file, creating folders. It never changes an existing file; it adds `-2`, `-3`… instead.
- **Cache:** `cache/channels.json`, with the date of each listing. `channels` reuses a listing fetched today; `search` reuses medians up to 14 days old (`--cache-days`). `--refresh` ignores it.
- **Requests:** one yt-dlp call per channel, phrase or title, plus the channel lookups in `search`. Lookups sleep 2–4 s apart, and a 429/403 gets one retry after 60 s. The call count is printed to stderr.

**Limits.**
- **Counts are approximate.** Views are YouTube's rounded display counts ("5.8M"). Ages are estimated from "2 weeks ago" text.
- **Search results aren't personal.** They're logged-out results, not what a viewer's home feed shows, and they vary by day and region.
- **`--popular` is expensive on big channels.** yt-dlp can't use the channel page's Popular sort, so the tool lists every upload (one page request per 30) and sorts locally.
- **A score shows a concept worked once.** It doesn't predict: the same concept reused on one channel can score far apart.
- **"Match" is crude keyword overlap.** Read the titles themselves.
