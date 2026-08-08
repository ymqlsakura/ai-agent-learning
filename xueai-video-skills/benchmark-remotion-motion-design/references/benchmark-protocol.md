# Remotion motion-design benchmark protocol

## 1. Fixed sample

Create one 30-second, 1920 by 1080, 30 fps sample with four narration-driven shots. Use the current XueAI series master aspect ratio. Test a separate 1080 by 1920 crop only when vertical publication is actually required.

1. Result hook, 0 to 6 seconds. Show a fast proof montage with a clear focal subject.
2. Real operation, 6 to 14 seconds. Show a real website or terminal and make the process visible.
3. Causal explanation, 14 to 23 seconds. Build a workflow or long-task loop node by node as it is spoken.
4. Resolution, 23 to 30 seconds. Land the result, one takeaway, and a restrained transition into the series identity.

Freeze these inputs before variant A:

- Spoken words and audio file.
- Cue frame for every phrase.
- Images, screenshots, video clips, and crop regions.
- Font files and typography scale.
- Brand colors and safe areas.
- Storyboard meaning and shot duration.

Only implementation vocabulary may change between variants.

## 2. Variants

### A-control

Use only the current XueAI master components. This measures the present baseline.

### B-official

Use official Remotion Agent Skills and the 4.0.506 effects, transitions, shapes, paths, Lottie, SFX, and optional Three integration.

### C-shotcraft

Start from B. Use two to four selected recipe cards. Read each recipe and its demo source before adaptation. Preserve the same storyboard and content.

### D-hybrid

Start from C. Add no more than two patterns from RVE or Prompt to Motion Graphics. This tests whether the extra library adds quality or only complexity.

### E-design-master-v2

Use the XueAI Design Master V2 with the same evidence pack. External libraries may contribute only audited local patterns. This variant tests whether the episode feels like one designed series while still showing real inputs, state changes, and results.

## 3. Automated checks

Run for every variant:

- Typecheck, lint, tests, and Remotion bundle.
- Full render twice with identical inputs.
- Frame extraction at every cue, midpoint, and final resting frame.
- Contact sheet generation.
- Text overflow and vertical safe-area checks.
- Cue-to-visual-change measurement. Target zero to six frames.
- Audio QC through `check-video-audio`.
- Render time, bundle size, and implementation time recording.

Automated motion audits are diagnostic only. A moving frame can still be a bad frame.

## 4. Hard gates

The scorecard uses these gates:

- `buildPass`
- `deterministicRender`
- `audioPass`
- `accurateMaterials`
- `safeReadableText`
- `cueSyncPass`
- `processVisible`

Any false gate makes the variant ineligible, regardless of aesthetic score.

## 5. Weighted review

Score each dimension from 0 to 10.

| Dimension | Weight | Review question |
|---|---:|---|
| `compositionHierarchy` | 20 | Is there one clear focal point with useful depth and spacing? |
| `motionIntent` | 15 | Does movement explain hierarchy, causality, or emotion? |
| `processVisibility` | 15 | Can a beginner see what happens step by step? |
| `narrationSync` | 15 | Do words and visible state changes arrive together? |
| `brandConsistency` | 10 | Does it feel like one XueAI series rather than mixed templates? |
| `contentClarity` | 10 | Can the viewer understand the point without rereading? |
| `reuseSpeed` | 10 | Can the pattern be reused quickly without brittle code? |
| `renderReliability` | 5 | Does it build, render, and remain deterministic? |

## 6. Blind viewing

Rename eligible outputs to random labels before showing them to the user. Do not reveal the stack name. Ask for:

- First choice.
- Most understandable process.
- Most premium design.
- Any moment that feels like PPT playback.
- Any effect that distracts from the words.

If two eligible variants differ by three points or less, the user's first choice wins.

## 7. Promotion rule

Promote only the smallest stack that delivers the winning quality. Classify every dependency as:

- Core for every episode.
- Optional for a specific shot type.
- Reference only.
- Rejected.

Update `produce-xueai-douyin-video` and `check-video-visual-experience` only after this decision.

Before calling the promotion complete, publish a new immutable version package according to `design-versioning.md` and append it to `design-version-registry.json`. Keep rejected candidates and their samples so the user can compare future versions against the real history.
