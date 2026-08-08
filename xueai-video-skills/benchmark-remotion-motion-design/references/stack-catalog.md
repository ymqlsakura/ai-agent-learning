# Motion stack catalog

## Core candidates

### Remotion official plugin and skills

Use as the technical foundation. It supplies current markup, effects, transitions, captions, rendering, Studio, and upgrade guidance. It improves correctness and access to current APIs, but it does not replace art direction.

Pinned Agent Skills version: `4.0.506`.

### video-shotcraft

Use as the primary shot-design vocabulary. It contributes recipe cards, tuned implementation demos, real-page capture guidance, 2.5D camera moves, rhythm, and sound design.

Use a recipe only after reading both its card and demo source. Inherit movement structure and timing, then reskin typography, color, material, and density to XueAI.

Do not turn every scene into a product-commercial shot. Use it for openings, proof montages, process reveals, UI demonstrations, and major transitions.

### Remotion effects and transitions

Use as finishing tools. Favor blur, progressive blur, glow, light trail, grain, paper texture, controlled distortion, and motivated transitions.

Limit each episode to a small transition family. More effects do not create better design.

### RVE Remotion templates

Use as a MIT-licensed component pantry. Good candidates include parallax pan, text highlight, Ken Burns, chart construction, and restrained logo reveals.

Do not copy the full visual style. Most templates are isolated primitives, not an episode-level design system. The pinned repository declares MIT in its README but has no LICENSE file. Full TypeScript checking also exposes plain-Remotion compatibility failures in templates that import `next/image` or use `style jsx`.

### Remotion Scenes

Use as a large motion vocabulary for text, shapes, backgrounds, data, UI, and transitions. Read the selected component source before adaptation.

Do not install the full repository into the episode master. Its pinned build bundles, but full lint and typecheck currently fail in `OgpVideo.tsx`. Its wide style range can also make one episode feel like several unrelated template packs.

### Curvable Motion

Use as the primary premium-design reference. Strong patterns include tonal backgrounds, restrained 2.5D card planes, unified accent mapping, clear resting frames, and focused type animation.

The 14 pinned components pass full TypeScript checking and package dry-run. Prefer an audited local adaptation or a small vendored component with MIT attribution. The package is not published to npm, so do not add an unpinned moving Git dependency to production.

### Remotion Playground

Use only as a learning reference. The pinned repository contains 38 Composition registrations, including audio waveform, spectrum, and volume examples.

Do not promote it to production. The main entry fails to bundle because `BrandShowcase.tsx` contains an unterminated string. The audio examples use generated sine values instead of actual audio analysis, and the repository has conflicting MIT and ISC license declarations.

### Prompt to Motion Graphics

Use as a pattern reference for kinetic typography, messaging UI, charts, sequencing, spring physics, social layouts, and 3D. Do not bring its SaaS runtime or prompt compiler into the video master.

## Default production recommendation to test

Core:

- XueAI series identity and episode structure.
- Official Remotion plugin and Agent Skills.
- XueAI Design Master V2 from `xueai-design-master-v2.md`.
- Curvable-inspired tonal fields, card depth, and restrained spatial motion.
- Existing XueAI audio and visual QC.

Optional by scene:

- video-shotcraft shot selection and tuned motion parameters.
- Official effects and transitions.
- One audited RVE or Scenes pattern.
- One audited Curvable component when the native XueAI primitive is not enough.
- Lottie for a supplied or approved animation.
- React Three Fiber for a shot that genuinely needs depth or camera movement.

Avoid by default:

- Installing all four external libraries into the master.
- Remotion Playground as a production dependency.
- Synthetic waveform examples when real audio data is available.
- Random effect stacking.
- A different transition on every cut.
- Generic card grids as the main visual language.
- Rebuilding real interfaces with fake UI.
- Continuous motion with no resting frame.

Exact upstream revisions are recorded in `source-lock.json`.

The 2026-08-05 installation, build, render, license, and visual findings are recorded in `library-evaluation-2026-08-05.md`.
