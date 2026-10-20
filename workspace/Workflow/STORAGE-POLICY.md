# Storage policy

Goal: keep what's needed for the best output plus a useful record, nothing else.

## Where things go

| Place | Holds |
| --- | --- |
| `Videos/<video>/` | **Everything about one video**: `01-Raw` originals, `02/03` audio and assets, `05-Exports/{Review,Final}`, `08-Analysis` transcripts, `09-Footage-Library`, `10-Project` (editable project), `11-Work` (dated working folders, **`11-Work/scratch/` for experiments**), `12-Archive` (closed-out archives), `BRIEF.md`, `RECORD.md` |
| `Videos/Shorts/` | One folder per short (`_Short-Template/`: `SHORT.md`, `raw/`, `project/`, `exports/`, `scratch/`) plus `RESULTS.md`. A short cut from a long video links to its source instead of copying the footage |
| `Workflow/` | Only general, reusable knowledge the user wants kept: `STYLE.md`, `LESSONS.md`, `Pipelines/` (playbooks), `Studies/` (created on first use), `Tactics/` (one folder per tactic; a source's example frames, transcript excerpts and ≤ 20 s clips go in its `examples/`, kept as private reference and out of git), `CHANNEL.md`, `Ideas.md` (curated idea backlog), `Ideas-Research/` (dated raw research output and pre-video briefs, created on first use), `Tools/` (their `cache/` and `ref-cache/` folders are regenerable and may be trashed any time), `COMPONENTS.md` |
| `Shared-Assets/` | Reusable music, SFX, fonts, brand files, with licences |
| `Incoming/` | Drop folder only. Once you have copied a file into `01-Raw` and verified the copy's hash, the Incoming copy can go to the trash (on the approval list). |

## While working

- **Scratch by default.** Probes, test renders, comparison clips and tool experiments go in `Videos/<video>/11-Work/scratch/`. At each milestone, keep what matters (one line in `RECORD.md` or the dated work folder) and trash the rest.
- **One current review render.** When a new review is verified, trash the previous one unless the user asked to keep it.
- **What may be trashed without asking:** only what the assistant generated itself in the current video's `11-Work/scratch/`, and review renders it made that a newer verified one replaced. Everything else (intermediates, `Incoming/` copies, anything the user made) goes on a list the user sees first.
- **No duplicate copies.** Use hardlinks or paths instead of copying media; don't keep review copies of finals.
- **Big intermediates** (EXR sequences, extracted frames, DNxHR/ProRes source copies) are regenerable from originals + recipe. Put them where they're fast (a fast internal SSD is fine) and propose trashing them once the stage they feed is verified.
- Keep ≥30 GiB free on each drive during batch work.

## Closing a finished video (`video-closeout` skill)

1. Write `RECORD.md` and propose lessons (the user confirms scopes).
2. Pack raw footage into two lossless 7-Zip archives in `12-Archive/`: recordings used in the final, and unused takes (outtakes). Verify every file against its SHA-256. Before the loose copies go, ask whether a second copy of the archives exists on another drive (after close-out the archives are the only copy).
3. Pack small logs/receipts into one `.tar.zst`; keep a few representative frames of any big sequence.
4. Show the user an exact list by category with sizes; move only approved items to the trash.
5. Verify the finals, the editable project's references and the archives afterwards; write the audit into the video's `RECORD.md` (or `12-Archive/audit.md`).

## Deleting

Assistants never permanently delete. Approved items go to the drive's trash (`gio trash` on Linux keeps it on the same drive, no copying; `trash` or Finder on macOS; the Recycle Bin on Windows). The user reclaims the space by emptying the trash. Always keep: originals (loose or in verified archives), finals, licences/credits, the editable project, recipes and small records. Never clear whole caches without checking what depends on them.

Note: 7-Zip barely shrinks phone video (~1%). Archives make one tidy file; real space savings come from removing regenerable intermediates and duplicates.
