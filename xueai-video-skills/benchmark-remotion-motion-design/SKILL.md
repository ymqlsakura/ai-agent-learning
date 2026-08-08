---
name: benchmark-remotion-motion-design
description: Compare Remotion motion-design skills, plugins, effects, templates, and shot systems with one fixed vertical-video sample. Use when selecting a production motion stack, benchmarking visual quality, testing a new Remotion skill, or deciding which motion components should enter the XueAI video master toolkit.
---

# Benchmark Remotion Motion Design

Use one fixed script, voice track, asset pack, storyboard, duration, and render profile. Change only the candidate motion stack. Do not compare unrelated creative directions.

## Workflow

1. Read `references/stack-catalog.md` to understand the role and boundary of every installed source.
2. Read `references/design-versioning.md` before changing or promoting the reusable design system.
3. Read `references/xueai-design-master-v2.md` before designing a production candidate.
4. Read `references/benchmark-protocol.md` before creating variants.
5. Freeze the benchmark pack. Record the script, cue frames, assets, fonts, colors, resolution, fps, and duration.
6. Produce the control first. It must use the current XueAI components without new motion libraries.
7. Produce the remaining variants from the same storyboard. Do not improve the copy or replace assets between variants.
8. Render each variant twice and compare hashes or sampled frames to verify deterministic output.
9. Run build, typecheck, audio QC, text-safe-area checks, cue checks, and contact-sheet generation.
10. Score the eligible variants with `scripts/score_benchmark.py`.
11. Hide variant names for the user's viewing test. The user's preference breaks close scores within three points.
12. Register the candidate with a new immutable `xueai-motion-vMAJOR.MINOR.PATCH` version. Never overwrite an earlier sample.
13. Promote the smallest winning stack. Keep specialist libraries optional instead of adding every dependency to the production master.

## External library intake

When the user names a component library or a video recommends one:

1. Identify the exact upstream repository. A display name is not sufficient when multiple repositories share it.
2. Pin the exact commit before installation.
3. Check the actual LICENSE file and package metadata. Record conflicts.
4. Run the upstream build, lint, typecheck, and official example without editing upstream source.
5. If the main project fails, preserve the error and isolate only the claimed component for a second test.
6. Render a visible out-of-box sample before making design judgments.
7. Adapt the best pattern to one fixed XueAI evidence pack. Do not compare unrelated copy or assets.
8. Classify the source as core, optional, reference only, or rejected.
9. Never install every candidate into production merely because the repositories are locally available.

## Required variants

- `A-control`: current XueAI Remotion toolkit only.
- `B-official`: official Remotion plugin, Agent Skills, effects, and transitions.
- `C-shotcraft`: variant B plus selected video-shotcraft recipe cards and tuned demos.
- `D-hybrid`: variant C plus only the strongest reusable patterns from the RVE and Prompt to Motion Graphics references.
- `E-design-master-v2`: the same evidence pack rebuilt with the XueAI Design Master V2 and only audited local adaptations.

For a newly named library, add one isolated library variant and one XueAI Design Master V2 adaptation. The isolated variant proves what the library does out of the box. The adaptation proves whether its best idea improves a real XueAI scene.

## Non-negotiable gates

Reject a variant when any of these is false:

- Project builds and renders without errors.
- Render is deterministic.
- Audio passes the XueAI audio QC skill.
- Every visual claim uses accurate material.
- Text stays inside the vertical-video safe area and remains readable on a phone.
- Narration cues and visible state changes stay within six frames unless the storyboard explicitly defines anticipation.
- The viewer can see the process, not just a sequence of completed cards.

Do not use transition count, particle count, or average pixel change as evidence of design quality. Motion must clarify hierarchy, causality, or emotion.

## Evaluation output

Produce:

- One MP4 file for every compared variant, with anonymous labels during blind review.
- One contact sheet per variant.
- One cue-alignment report.
- One completed scorecard JSON.
- One Markdown ranking from `scripts/score_benchmark.py`.
- A recommendation split into core stack, optional modules, rejected modules, and reasons.
- One immutable version package containing the winning sample, contact sheet, QC report, hashes, commits, parent version, and user selection status.
- An updated `references/design-version-registry.json`. A reusable design change is not complete until this registry is updated.

## Scripts

- Run `scripts/install_stack.ps1` to recreate project-local links and pinned reference caches.
- Run `scripts/verify_stack.ps1` after installation or upgrades.
- Run `scripts/score_benchmark.py --input <scorecard.json> --output <ranking.md>` after review.
