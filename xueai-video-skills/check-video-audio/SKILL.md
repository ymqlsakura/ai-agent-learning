---
name: check-video-audio
description: Deterministic audio quality control for recordings, narration tracks, and rendered videos. Use whenever Codex receives or produces voice audio, edits a Remotion video, prepares a video export, or is asked to inspect loudness, background noise, fixed high-frequency tones, feedback squeal, hum, clipping, channel faults, or audio-video duration. Run it on the raw recording, the processed narration, and the final render before delivery or publication.
---

# Check Video Audio

Treat audio QC as a blocking production gate. Do not approve a video from a volume meter alone.

## Required workflow

1. Run the checker on the raw recording:

```powershell
python scripts/check_audio.py "D:\path\recording.mkv" --profile recording --strict
```

2. Process a derivative file when the recording fails. Never overwrite the source.
3. Run the checker on the processed narration:

```powershell
python scripts/check_audio.py "D:\path\narration.wav" --profile narration --strict
```

4. Mix narration, music, and effects, then run the checker on the final render:

```powershell
python scripts/check_audio.py "D:\path\final.mp4" --profile final --strict
```

5. Deliver or publish only after every required gate passes.

## Blocking rules

- Reject clipping, unsafe true peaks, missing audio, severe channel imbalance, or phase inversion.
- Reject persistent narrow high-frequency tones and feedback squeal. Natural consonants and normal speech harmonics are not defects.
- Reject a measurable noise floor above the selected profile limit.
- Reject final loudness outside the delivery range.
- Reject material audio-video start or duration mismatch.
- Treat warnings as failures when `--strict` is used.

Read [references/quality-standard.md](references/quality-standard.md) only when thresholds need interpretation or adjustment.

## Review requirements

After an automatic pass, perform a short headphone review at normal and elevated playback volume. Listen to:

- At least one quiet pause.
- The loudest detected passage.
- Any timestamps named by the checker.
- Sentence endings and breaths after denoising or expansion.

If listening contradicts the numeric result, listening wins. Record the issue, adjust the processing conservatively, and rerun the checker.

## Repair rules

- Diagnose the source before adding stronger filters.
- Prefer a narrow notch for a fixed tone and a high-pass filter for low-frequency rumble.
- Use gentle spectral denoising and a slow-release expander for stationary analog noise.
- Avoid strong denoising that makes speech muffled, metallic, or watery.
- Recheck the repaired derivative with the same profile.

## Output contract

The checker prints `PASS`, `WARN`, or `FAIL`, followed by findings and measured values. Exit code `0` means pass, `1` means a quality gate failed, and `2` means the file or environment could not be analyzed.

Use `--json` for automation and `--report-json <path>` to save a machine-readable report.
