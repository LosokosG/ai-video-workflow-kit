---
name: video-closeout
description: Use when the user approves a final video or says a video is done, finished or final, or asks to clean up a finished video's files, archive its raw footage or free disk space after a video.
---

# Closing a finished video

Goal: a video folder that holds the finals, the editable project, archived originals and a one-page record. Knowledge worth keeping moves into `Workflow/`; generated leftovers go to the trash with the user's approval.

## Steps

1. **Protect the finals.** Check `05-Exports/Final/` has the files, the music/asset credits and a checksum manifest. Record their SHA-256 in the video's `RECORD.md` (or `12-Archive/audit.md`).
2. **Write `RECORD.md`** from the template: status, finals, where everything is, decisions and the user's words, techniques used (link the playbook), tactics used with timestamps, what we'd do differently, how to restore.
   - Keep the **final-timeline transcript and chapter list** next to the finals (`05-Exports/Final/`); `video-performance` lines the retention graph up with them.
   - Set every tactic used in the final from `candidate` to `used` (its "Used in" line gets a "published" entry once the video is public), then run `python3 Workflow/Tools/tactics/build_index.py`.
   - Final thumbnails and titles come from `video-packaging` (final mode).
3. **Propose lessons** with `video-lessons`, as one table the user can mark (all videos / this setup / this video only).
4. **Archive originals:** list the `01-Raw` files the final uses (from the edit's source mapping), then run `python3 Workflow/Tools/closeout/archive_raw.py <video-dir> <used-list>`. It builds `raw-footage-used-in-final.7z` and `outtakes-unused-takes.7z` and verifies every file by hash. Tell the user 7-Zip saves only ~1% on phone video; it's for tidiness.
5. **Pack small records:** thousands of receipts or logs into one `12-Archive/*.tar.zst`. For big frame sequences worth remembering, keep first, middle and last frames.
6. **Build the cleanup list** by category with sizes (sizes that count hardlinks correctly): regenerable intermediates, duplicates (hash-verified), superseded renders and variants, loose raw after the verified archives, and any `Incoming/` copies. Check that nothing on the list is referenced by the editable project or the finals.
7. **Ask the user** with a plain-language summary per category (what it is, what it costs to get back). If they're unsure what something is, explain its practical value in simple terms before asking again.
8. **Trash approved items**, one category per command, to the OS trash (`gio trash` on Linux). Never `rm` user media, never empty the trash. Before loose originals go, ask whether the archives have a second copy on another drive; offer to copy them to one the user names.
9. **Move video-specific material** still under `Workflow/` into the video folder (`10-Project`, `11-Work`). Rewrite paths, fix symlinks, and save the old → new map in `RECORD.md` (or `12-Archive/audit.md`).
10. **Verify and report:** finals' hashes unchanged, project references resolve (except files now inside archives), archives verified. Update `Workflow/CURRENT-EDIT.md`: "awaiting publish → numbers at d7 and d28 (`video-performance`)", with the video folder. Tell the user how much is in the trash and which older, unrelated items are also in it, since emptying the trash deletes everything there.
