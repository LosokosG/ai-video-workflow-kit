# Tools

| Tool | Use |
| --- | --- |
| `study/study.py` | Fetch captions, metadata, thumbnail and most-replayed heatmap; download verified clips, audio or whole videos; frames and time-stamped contact sheets; cuts, new-element onsets, stillness and loudness; pauses and speech rate; local transcription with first-word time (all with time ranges); tactic example folders (`examples`). Used by `video-study`, `video-intro`, `retention-review` |
| `stems/` | Split a music track into drums / bass / melody / vocals (Demucs, CPU); see its README |
| `hyperframes-lint/hf_lint_hook.py post / stop / check [DIR]` | HyperFrames lint gate with the project's pinned CLI (or `Workflow/hyperframes-pin.txt`, else `latest`). Claude Code runs it through hooks (`.claude/settings.json`: after edits, and before a turn ends); Codex reads `.codex/config.toml`; otherwise run `check` by hand. Errors and unaccepted warnings must be fixed; accept deliberate warnings in `<project>/.hyperframes-lint-accept`. Projects inside `scratch/` folders are skipped (probes, not deliverables) |
| `tactics/tactics.py find / show / core / build` | Load only the tactics a step needs: filtered search (format, stage, face, mode, text), a ~80-word working card per tactic (`--full` for examples), the core checks; `build` regenerates the routers and `Tactics/picks/` |
| `tactics/build_index.py` | Rebuild the pick list in `Tactics/INDEX.md` from every `TACTIC.md` (after adding a tactic or changing a status) |
| `tactics/apply_polish.py EDITS.json` | Apply a JSON of tactic edits (pick lines, roles, field rewrites) to many `TACTIC.md` files at once |
| `closeout/archive_raw.py VIDEO_DIR USED_LIST` | Pack a finished video's raw footage into verified used/outtakes 7-Zip archives (`video-closeout` skill) |
| `ideas/outliers.py channels / search / exists …` | Outlier scores (views ÷ channel median) from yt-dlp listings, no login: a channel's latest uploads, desire-phrase search, originality search; see its README (`video-ideas`, `video-packaging` skills) |
| `packaging/feedcheck.py CANDIDATE… --title T --ref-search Q --out DIR` | Thumbnail check sheet: the candidate in a mock desktop and mobile feed among current niche thumbnails, greyscale, no-title and tiny sizes, proxy numbers; see its README (`video-packaging` skill) |

Tool requirements: Python 3.10+, `ffmpeg`/`ffprobe`, `yt-dlp` (study, ideas, packaging), `faster-whisper` (local transcription in `study.py`; set `WHISPER_MODEL` to a model name or folder, `WHISPER_PY` to the interpreter that has it), Pillow (`packaging/feedcheck.py`), `7z` (`closeout`), Node 22+ with `npx` (HyperFrames lint), Demucs only for `stems/`. `docs/SETUP.md` lists install commands per OS. If Pillow or faster-whisper live only in the workflow venv (`Workflow/Tools/.venv`), run those tools with its Python (e.g. `Workflow/Tools/.venv/bin/python Workflow/Tools/packaging/feedcheck.py …`).
