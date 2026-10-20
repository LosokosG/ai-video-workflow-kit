---
name: video-lessons
description: Use when video work taught something worth keeping (a fix that took long to find, a user correction or stated preference, a technique that worked or failed), when the user confirms, changes or retires a lesson, or at the end of a video.
---

# Keeping LESSONS.md current

`Workflow/LESSONS.md` is the workspace's memory of rules learned on real videos. Agents scan its headings at the start of a task, so every entry must be short, specific and backed by what actually happened.

## Is it a lesson?

Write one only when both are true: it would change how a future video is made, and the situation will come back. Otherwise it goes elsewhere:

| What you learned | Where it goes |
| --- | --- |
| A fact about this video only | that video's `RECORD.md` |
| Step-by-step technique detail | a playbook under `Workflow/Pipelines/` |
| A taste preference the user stated | `Workflow/STYLE.md` |
| A rule that changes future work | `Workflow/LESSONS.md` (this skill) |

## Entry format

```
## <Rule, phrased as an instruction>
- **Context:** the stage, footage or tool setup where it applies
- **Problem:** what went wrong, or what took long, without the rule
- **Rule:** what to do instead
- **Scope:** all videos | <a named setup, e.g. "this mic and room"> | <one video> · **Status:** proposed | confirmed | context default | starter default | superseded by "<title>"
- **See:** (optional) files someone would open to apply it
- **Evidence:** what happened, the user's words if they set the rule, and the paths to the proof
```

## Procedure

1. **Draft it yourself** from the session's evidence (measurements, renders, the user's corrections). The user reviews; they don't write.
2. **Propose a scope.** Prefer the narrowest scope the evidence supports; a number measured on one mic is not a rule for every mic.
3. **Search first.** If an entry already covers the rule, edit it instead of adding a second one.
4. **Set the status from the user's answer:** agreed → `confirmed` with the scope they accept; true only for a setup → `context default`; no answer yet → `proposed`.
5. **Never silently overwrite a rule.** When a better method replaces one, mark the old entry `superseded by "<new title>"` and keep it so the change can be rolled back. Delete an entry only when the user says it was wrong.
6. **At the end of a video,** collect every new or changed lesson into one table (title · proposed scope · status) so the user can answer them in a single message.
