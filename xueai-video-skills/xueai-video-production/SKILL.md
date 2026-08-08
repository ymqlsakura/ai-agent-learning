---
name: xueai-video-production
description: Orchestrate the complete XueAI Learning AI for 1000 Days video workflow from script discussion through continuous narration, semantic audio editing, strict audio QC, traceable asset sourcing, narration-cued Remotion motion design, complete visual QC, companion notes, versioning, and archive. Use whenever Codex starts, continues, repairs, reviews, or finishes a DayXX episode, XueAI Douyin video, or reusable series-video production workflow.
---

# XueAI Video Production

Run one traceable production pipeline. Do not treat script, audio, assets, Remotion, and QC as separate improvisations.

## System ownership

- Keep the reusable Remotion system, commands, tests, design primitives, and series documents in `D:\video\_系统\remotion-base`.
- Keep only episode-specific script, context snapshot, raw and edited audio, timestamped transcript, shot cues, material ledger, local assets, renders, and QC reports in `D:\video\dayXX`.
- Never copy reusable React components or maintenance scripts into a Day directory to make one episode pass.
- Treat the Git-managed copy of this Skill as the methodology source and `D:\video\.codex\skills\xueai-video-production` as its installed workspace entry.

## Non-negotiable rules

- Read the series context before discussing content. The formal first production step remains script discussion.
- Create one Markdown script working file as soon as discussion starts. Apply every revision to that file.
- Let the episode structure follow the topic. Never force a fixed number of sections.
- Keep non-spoken directions in explicit `分镜：`、`素材：`、`搜索：`、`来源：`、`署名：`、`使用：` or `制作备注：` lines.
- Use one continuous human recording by default. Edit false starts, repeated takes, and long pauses after recording.
- Preserve raw recordings and source assets. Create derivatives instead of overwriting originals.
- Give every release candidate an immutable `dayXX-rN` version and every reusable design-system change an immutable `xueai-motion-vMAJOR.MINOR.PATCH` version.
- Treat the approved narration as the timing master for Remotion.
- Show input, process, and result for every action-oriented claim. Static slides cannot replace a real process.
- Automatically collect legal, traceable public materials when no new authority is required. Do not wait for the creator to do work the system can safely complete.
- Classify every planned asset as `evidence` or `illustration`. Generated images, generic stock footage, text cards, and reconstructed interfaces cannot replace missing evidence.
- When creator-owned evidence is required and unavailable, create a precise material request and move the affected shot to `blocked-user-material`. Do not build or approve that shot until the asset arrives or the creator explicitly changes the claim.
- Record source, license, generation metadata, and local path for every external asset.
- Run audio QC on raw recording, edited narration, and final render.
- Run visual QC on the complete final render with audio. A contact sheet alone cannot approve publication.
- Do not publish while any P0 or P1 remains. Re-render and recheck the new file after every blocking fix.
- Commit every verified milestone to Git. Never commit credentials, voice references, private screenshots, or unlicensed media.

## Required references

- Read [references/series-and-script.md](references/series-and-script.md) before topic selection or script work.
- Read [references/audio-production.md](references/audio-production.md) before recording, voice generation, editing, or mixing.
- Read [references/materials-and-remotion.md](references/materials-and-remotion.md) before asset collection or Remotion implementation.
- Read [references/motion-design-system.md](references/motion-design-system.md) before storyboarding, implementing motion, or auditing a rendered scene.
- Read [references/quality-and-iteration.md](references/quality-and-iteration.md) before preview review, final render, or release.
- Read [references/versioning-and-selection.md](references/versioning-and-selection.md) before naming a candidate, comparing visual systems, or declaring a reusable method settled.
- Copy [assets/episode-production-record.md](assets/episode-production-record.md) into the Day directory when the project does not already provide an equivalent `制作清单.md`.
- Copy [assets/shot-cue-sheet.template.json](assets/shot-cue-sheet.template.json) and [assets/material-registry-template.md](assets/material-registry-template.md) when the episode has no equivalent machine-readable cue sheet and traceable ledger.
- Copy [assets/material-request-template.md](assets/material-request-template.md) when any required creator-owned evidence is missing.

Use `check-video-audio` for deterministic audio gates and `check-video-visual-experience` for the final visual experience gate. Those Skills are mandatory children of this workflow. Consult `remotion-best-practices`, `video-shotcraft`, `remotion-transitions`, and `benchmark-remotion-motion-design` before changing the reusable motion system.

## Production state machine

Use these states in the production record:

```text
planning
  -> script-discussion
  -> script-approved
  -> audio-received
  -> narration-approved
  -> materials-ready
  -> remotion-draft
  -> qc-fixing
  -> release-candidate
  -> released
```

Move forward only when the current gate passes. When a later finding invalidates an earlier assumption, move back to the earliest affected stage.

Use `blocked-user-material` as a temporary blocking state at Stage 3 or Stage 4. Resume only after the requested evidence is received and approved, or after the creator explicitly approves a script or claim change.

## Stage 0. Prepare the workspace

1. Read the series context, visual style, previous related episodes, and current production record.
2. Inspect the target Day directory before creating files.
3. Create a feature branch or worktree before changing code or reusable templates.
4. Create the Day workspace when it does not exist:

```powershell
cd D:\video\_系统\remotion-base
npm run episode:new -- --day 32 --topic "主题" --date 2026-08-01
```

5. Preserve `创作背景.md` as the episode context snapshot.

Gate: one Day directory, one script working file, one production record, and a clean version-control baseline exist.

## Stage 1. Discuss and approve the script

1. Define the target beginner, real problem, promised result, proof, free companion document, and next-episode bridge.
2. Write a result-first hook with visible evidence.
3. Place the fixed series line after the hook and before the main content.
4. Organize numbered viewer-facing points according to the current topic.
5. Keep installation details, command tables, and long procedures in the companion note when the video only needs the key judgment.
6. Add the fixed free-document sentence once at a natural value point.
7. End with a concrete next-episode preview.
8. Iterate in the same Markdown file until the user approves the spoken copy.
9. After spoken copy approval, add shot and material lines to the same file.

Gate: the user approves the spoken copy, every required fixed line exists, every claim has a planned proof, and non-spoken notes are unambiguous.

Rollback: if recording exposes awkward wording or unsupported claims, return to the script file, revise it, and record the change before editing audio.

## Stage 2. Produce and approve narration

1. Receive one continuous human recording by default.
2. Run the raw-recording audio gate before editing.
3. Transcribe and align the recording to the approved script.
4. Remove false starts, duplicate takes, verbal mistakes, and excessive pauses while preserving natural, friendly phrasing.
5. Use whole-sentence or whole-clause cuts, short crossfades, and conservative silence trimming.
6. Apply optional speed adjustment only after the clean edit. Keep speech natural.
7. Use authorized IndexTTS only for explicit patches or an explicitly authorized full draft.
8. Process a derivative with conservative high-pass filtering, denoising, expansion, compression, and loudness normalization when required.
9. Run the narration audio gate and produce a timestamped transcript.
10. Let the user listen to the final narration before picture lock.

Gate: narration strict QC passes, the transcript contains no wrong take or missing sentence, splice points are clean, and the user accepts pacing and emotion.

Rollback: source defects return to recording or a local patch. Processing artifacts return to the clean edit, not to stronger filters.

## Stage 3. Build the shot and material plan

For every semantic beat, record:

- narration claim,
- viewer task,
- visible input,
- visible process or state change,
- visible result or evidence,
- asset source,
- asset role: evidence or illustration,
- acquisition owner: automatic or creator,
- fallback permission,
- expected duration,
- source and license status,
- production status.

Generate the episode and material ledger when applicable:

```powershell
npm run episode:from-script -- --script "D:\video\day32\Day32-主题-文案初稿.md" --date 2026-08-01
npm run episode:materials -- --config "D:\video\day32\video\episode.json"
```

Gate: every spoken claim has a visual job, every action-oriented claim has an input-process-result plan, and every required asset has an acquisition owner. Missing creator evidence has a written request instead of a fake fallback.

Rollback: missing proof returns to the script if the claim should be removed, or to material sourcing if proof can be acquired.

## Stage 4. Collect, generate, and approve materials

1. Search and capture all legal, traceable materials that can be acquired automatically, including official pages, public webpages, approved stock libraries, and authorized generation sources.
2. Prefer creator-owned recordings, projects, websites, and data for claims about the creator's work, accounts, audience, customers, or results.
3. Capture real webpages and interaction states, not search thumbnails.
4. Prefer official and first-party material for product behavior and commands.
5. Use Pexels for generic people and environments with source and creator records.
6. Use Codex or ComfyUI images for emotion and metaphor, not fake product evidence.
7. Use paid API video only after confirming model, duration, framing, and cost.
8. When creator evidence is missing, record the exact claim, requested capture, privacy treatment, technical format, and production impact in the material request queue. Ask the creator for that asset immediately.
9. Do not replace missing creator evidence with a text card, fake interface, generated image, unrelated ambience, or an unapproved reconstruction.
10. Use `流程演示` or `官方资料还原` only after the creator explicitly approves that treatment. The label does not turn a reconstruction into evidence.
11. Save every selected asset under the Day directory and update its ledger status.
12. Reject watermarks, unclear rights, private data, invalid metrics, unreadable pages, and assets that only decorate unrelated narration.

Gate: all required evidence and illustration assets exist locally, are readable, map to exact narration, and have source or generation records. The request queue has no unresolved item needed by the current cut. Paid and external assets have the required authorization.

## Stage 5. Build the Remotion video

1. Sync the approved narration and use its real duration as the timeline master:

```powershell
npm run episode:validate -- --config "D:\video\day32\video\episode.json"
npm run episode:sync -- --config "D:\video\day32\video\episode.json"
```

2. Split visuals by spoken meaning and natural pauses, not by a fixed chapter grid.
3. Reuse the fixed series opener and visual system.
4. Show real process for websites, terminals, Agent work, and automation.
5. Give each shot one primary motion purpose. Use staged reveal, typing, scrolling, cursor movement, current-step highlighting, before-and-after state, or restrained camera movement.
6. Build item-level cue times from the final narration. Reveal each list item, command, comparison, or workflow node when it is spoken. Keep future details hidden.
7. Select a proven semantic pattern for each scene: word-relay filmstrip, terminal typewriter, process cascade, evidence zoom, before-and-after comparison, or restrained group-photo outro. Do not use the same card entrance for every scene.
8. For an operation, show the state changing across time. A cursor loop, slow zoom, moving glow, or animated subtitle does not count as process evidence.
9. Do not allow three consecutive static presentation shots or an unjustified unchanged information scene longer than 5 seconds.
10. Generate subtitles from the approved narration, then correct names, commands, spacing, and grammar manually.
11. Keep subtitles and important evidence inside platform-safe regions.
12. Add music only when title, creator, source, and commercial-use rights are recorded.
13. Render targeted stills and short sections for critical screens before a full render.

Gate: the draft covers the complete narration, fixed series elements are correct, the process is visible, subtitles are accurate, and no placeholder or unapproved asset remains.

## Stage 6. Review the draft

1. Render a review draft and a shot manifest.
2. Check every shot at start, middle, and end.
3. For progressive text and workflows, inspect the frame immediately before and after every narration cue. Reject future items that appear early.
4. Run the generic motion audit with the episode shot-cue manifest. Treat it as a near-static detector, not proof of good storytelling.
5. Watch key demonstrations at normal speed with audio.
6. Check the first 30 seconds, fixed series line, free-document prompt, important examples, and next-episode preview.
7. Collect revisions by exact time range and severity.
8. If narration changes, return to Stage 2 and resync the complete timeline.

Gate: no known content, timing, subtitle, privacy, or process-visibility blocker remains before the release render.

## Stage 7. Render the release candidate

1. Run project lint, tests, type checks, and bundle checks.
2. Render 1920 x 1080 at 30 fps unless the episode specifies an approved alternative.
3. Assign the next immutable candidate version such as `day32-r3` before rendering.
4. Archive the previous candidate in a recoverable `_superseded` directory before changing the canonical filename.
5. Keep the versioned file and a stable main filename such as `day32-final.mp4`. The stable name may point to the selected version, but it cannot replace the versioned artifact.
6. Record the candidate version, design-system version, parent candidate, duration, file size, codec information, frame rate, SHA256, and Git commit.

Gate: the release candidate fully decodes, starts correctly, contains the approved narration, and has a unique recorded hash.

## Stage 8. Run complete QC and iterate

Run all gates on the new release candidate:

1. Content and transcript alignment.
2. Subtitle correctness and safe-area review.
3. `check-video-audio` with the `final` profile and strict mode.
4. `check-video-visual-experience` on the complete video with audio.
5. Full decode, black-frame, duration, A/V sync, missing-asset, and source-ledger checks.
6. Independent QC against the exact new file hash.
7. Human headphone review at normal and elevated volume.

For each loop:

```text
inspect -> classify -> fix root cause -> run tests -> render affected section
-> render new full candidate -> rerun all affected gates -> update record
```

Do not reuse an approval from an older file. Continue until P0 and P1 are zero. Close P2 that affects comprehension, sound, visible polish, or series consistency. Record any intentionally accepted cosmetic P2.

## Stage 9. Prepare companion material and release package

1. Turn the approved script into a beginner-friendly companion note.
2. Include the promised xueai.me documentation links, screenshots, commands, and examples.
3. Update the target Feishu document when requested.
4. Confirm that the free document exists before the video promises it.
5. Prepare source attribution, cover, title, description, and next-episode note.
6. Package the final video, QC reports, transcript, material ledger, and validation record.

Gate: the release package matches the video promise and contains no private credentials or unlicensed material.

## Stage 10. Release and archive

1. Ask for explicit authority before publishing or changing an external production system.
2. Preserve raw recording, approved narration, source ledger, final script, final video, reports, and Git history.
3. Mark the production record `released` only after the uploaded file is verified.
4. Record lessons that should change the reusable workflow. Update this Skill or the project guide instead of leaving them only in chat history.
5. If the reusable visual system changed, publish a new `xueai-motion-vMAJOR.MINOR.PATCH` package with a sample, contact sheet, QC report, hashes, parent version, differences, and selection status.
6. Never overwrite or delete a rejected design version. Keep it available for future visual comparison.

## Completion contract

Report completion only when:

- the approved script and final narration match,
- narration and final-render audio gates pass,
- every key action shows input, process, and result,
- visual QC has P0 0 and P1 0,
- technical decode and synchronization pass,
- all used materials are traceable and authorized,
- no required evidence is missing, substituted, or left in `blocked-user-material`,
- companion material promised in the video exists,
- the exact final file hash is recorded,
- the final file has an immutable `dayXX-rN` version and records the exact `xueai-motion` version it used,
- every reusable method change has a new registered design version with directly viewable comparison artifacts,
- the Git worktree is clean and milestones are committed,
- the remaining human or external publication action is stated explicitly.
