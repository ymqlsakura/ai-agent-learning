# XueAI video audio quality standard

These thresholds are production gates for the XueAI short-video workflow. They are deliberately stricter than a basic intelligibility check.

## Profiles

### Recording

- Use for the untouched OBS recording.
- Aim for a true peak between -18 and -6 dBTP.
- Aim for active speech RMS between -34 and -18 dBFS.
- Require enough clean pauses to estimate background noise.
- A failed noise gate means the recording needs source correction or post-processing before editing. It does not require discarding the take automatically.

### Narration

- Use after high-pass filtering, denoising, compression, and narration normalization.
- Target integrated loudness from -18 to -14 LUFS.
- Target true peak from -4 to -1.5 dBTP, with -1 dBTP as the hard ceiling.
- Require noise floor at or below -58 dBFS for a clean pass. Above -52 dBFS is a hard failure.
- Require estimated speech-to-noise ratio of at least 30 dB for a clean pass. Below 24 dB is a hard failure.

### Final

- Use after narration, music, and effects are mixed.
- Target integrated loudness from -17 to -14 LUFS. Outside -19 to -13 LUFS is a hard failure.
- Target true peak from -3 to -1.5 dBTP, with -1 dBTP as the hard ceiling.
- Inspect fixed tones, clipping, channels, and synchronization even when continuous music prevents a reliable silence-floor estimate.

## Abnormal high frequency

Do not remove all high-frequency content. Speech needs consonants and air. Reject a narrow tone when it remains at nearly the same frequency across multiple time windows, has strong prominence over neighboring frequencies, and is loud enough to be audible. This catches the day29-style 10 kHz line without flagging normal speech harmonics.

## Bottom noise

Estimate the floor from the quietest short windows only when the program has enough dynamic range and at least one second of usable pauses. If music fills the entire final mix, validate the processed narration separately and mark final-mix floor measurement as unavailable instead of inventing a number.

## Feedback and hum

- Treat a recurring narrow tone from 2 kHz to 18 kHz as possible feedback or electronic oscillation.
- Inspect 50 Hz, 60 Hz, and their early harmonics for mains hum.
- A noise gate can hide noise only during pauses. It does not remove noise under speech.

## Release gate

- `FAIL` blocks delivery.
- `WARN` blocks delivery in strict mode and requires targeted listening otherwise.
- `PASS` still requires a short headphone review because perceptual artifacts can escape numeric tests.
