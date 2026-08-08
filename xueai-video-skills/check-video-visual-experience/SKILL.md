---
name: check-video-visual-experience
description: Review rendered educational and product videos for visual comprehension, process visibility, motion restraint, narration alignment, evidence accuracy, pacing, and release readiness. Use whenever Codex creates, edits, reviews, or prepares a Remotion video, tutorial, product demo, AI workflow video, or short-form educational video for publication. Run it on the final rendered video, not only on source code or a contact sheet.
---

# Check Video Visual Experience

Treat visual comprehension as a blocking release gate. A technically correct video still fails when the audience sees a sequence of static presentation slides but cannot see what happened.

## Required workflow

1. Read the final script, timeline, and asset ledger.
2. Watch the complete final render with audio.
3. Build a claim-to-picture audit for every action-oriented sentence:
   - input or starting state,
   - visible action or state change,
   - result or evidence,
   - exact time range.
4. Review every shot at its start, middle, and end. A midpoint contact sheet alone cannot prove that motion or process exists.
5. Build a narration cue table for every list, command group, workflow, comparison, and diagram. Record the spoken timestamp and reveal frame for each visible element.
6. Inspect the frame immediately before and after every important cue. Future points must not be visible before the narration reaches them unless the narration intentionally previews the full structure.
7. Inspect key demonstrations at normal playback speed. Verify that viewers can follow the action without guessing.
8. Run the audio QC skill separately. Visual approval does not replace audio approval.
9. Report P0, P1, and P2 findings. Do not approve publication while any P0 or P1 remains.
10. After fixes, review the newly rendered full video again. Do not reuse conclusions from an older render.

Read [references/visual-quality-standard.md](references/visual-quality-standard.md) when scoring process coverage, motion, pacing, or presentation-like scenes.

## Blocking rules

Mark as P1 and reject publication when any of these occurs:

- The narration explains a process, but the picture shows only a title, bullet list, abstract illustration, or final result.
- A product or website capability is claimed without showing the relevant page, interaction, state change, or verifiable result.
- A command is introduced without showing the command, what it starts, and the important result.
- Three or more consecutive shots behave like static presentation slides.
- A static information scene stays visually unchanged for more than 5 seconds without a justified reading need, speaker performance, or visible process.
- Decorative motion is busy enough to compete with the spoken point, subtitles, or evidence.
- A key click, input, result, comparison, or diagram step appears too briefly to understand.
- A list, command group, or workflow shows future points before the narration reaches them, causing the picture to get ahead of the explanation.
- Text is revealed on an evenly divided timer when the spoken timestamps are available and materially different.
- The visual contradicts the narration, uses the wrong asset, hides critical evidence, or exposes invalid data.

## Motion policy

- Give each shot one primary motion purpose.
- Use motion to reveal sequence, direct attention, compare states, or prove an action.
- Prefer staged highlights, cursor movement, scrolling, typing, progressive diagrams, before-and-after changes, and restrained camera movement.
- Reveal the current word, command, node, or card when it is spoken. Keep completed elements visible with lower emphasis and keep future elements hidden.
- Keep entry motion short, then provide a stable reading window.
- Avoid making every card, word, icon, and background move at the same time.
- Do not add motion to compensate for missing process footage. Acquire or create the missing process first.
- Use hard cuts for continuous real operations when they preserve clarity. Motion is not required at every cut.

## Process-first visual rules

- For websites and apps, show the page, the operation, and the resulting state. Use real screen recording when possible.
- For terminal workflows, show input, execution or progress, and the useful output. Mask private or unsafe status text.
- For automated tasks, animate the loop or timeline and show at least one real execution artifact.
- For data claims, show the source and highlight the exact value when it is spoken.
- For comparisons, keep both states visible long enough to understand what changed.
- For abstract explanations, animate causal steps instead of presenting several unrelated text cards.
- Use generated images for emotion or metaphor, not as a substitute for a process that should be demonstrated.
- Temporal pixel change is diagnostic evidence only. A moving cursor, subtitle, slow zoom, or decorative glow cannot by itself prove that a shot explains the process.

## Output contract

Return:

1. Release recommendation.
2. P0, P1, and P2 counts.
3. A process coverage table with time range, narration claim, visible input, visible process, visible result, and verdict.
4. Static-slide findings, including consecutive slide count and unchanged durations.
5. Motion findings, including excessive motion and missing motion.
6. Narration, subtitle, asset, and evidence alignment findings.
7. Exact repair instructions for each P0 and P1.
8. Narration cue evidence for each progressive text or workflow scene, including frames immediately before and after the cue.

State separately whether the full render was watched with audio, whether key processes were reviewed at normal speed, and whether the result is based only on sampled frames.
