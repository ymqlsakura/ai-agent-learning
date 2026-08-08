#!/usr/bin/env python3
"""Deterministic audio QC for recordings, narration, and final video renders."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
except ImportError as exc:
    raise SystemExit("numpy is required. Install it before running audio QC.") from exc


SAMPLE_RATE = 48_000
CHANNELS = 2
FLOAT_BYTES = 4
SECOND_BYTES = SAMPLE_RATE * CHANNELS * FLOAT_BYTES


PROFILES: dict[str, dict[str, float | bool | None]] = {
    "recording": {
        "lufs_warn_low": None,
        "lufs_warn_high": None,
        "lufs_fail_low": None,
        "lufs_fail_high": None,
        "true_peak_warn_low": -18.0,
        "true_peak_warn_high": -6.0,
        "true_peak_fail_low": -30.0,
        "true_peak_fail_high": -1.0,
        "noise_warn_above": -50.0,
        "noise_fail_above": -45.0,
        "snr_warn_below": 25.0,
        "snr_fail_below": 18.0,
        "active_rms_low": -34.0,
        "active_rms_high": -18.0,
        "require_noise_measurement": True,
    },
    "narration": {
        "lufs_warn_low": -18.0,
        "lufs_warn_high": -14.0,
        "lufs_fail_low": -20.0,
        "lufs_fail_high": -13.0,
        "true_peak_warn_low": -4.0,
        "true_peak_warn_high": -1.5,
        "true_peak_fail_low": -8.0,
        "true_peak_fail_high": -1.0,
        "noise_warn_above": -58.0,
        "noise_fail_above": -52.0,
        "snr_warn_below": 30.0,
        "snr_fail_below": 24.0,
        "active_rms_low": None,
        "active_rms_high": None,
        "require_noise_measurement": True,
    },
    "final": {
        "lufs_warn_low": -17.0,
        "lufs_warn_high": -14.0,
        "lufs_fail_low": -19.0,
        "lufs_fail_high": -13.0,
        "true_peak_warn_low": -3.0,
        "true_peak_warn_high": -1.5,
        "true_peak_fail_low": -8.0,
        "true_peak_fail_high": -1.0,
        "noise_warn_above": -58.0,
        "noise_fail_above": -52.0,
        "snr_warn_below": 30.0,
        "snr_fail_below": 24.0,
        "active_rms_low": None,
        "active_rms_high": None,
        "require_noise_measurement": False,
    },
}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    timestamp_seconds: float | None = None


class AnalysisError(RuntimeError):
    pass


def dbfs(value: float) -> float:
    return 20.0 * math.log10(max(abs(value), 1e-15))


def power_db(value: float) -> float:
    return 10.0 * math.log10(max(value, 1e-30))


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def require_tools() -> tuple[str, str]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AnalysisError("ffmpeg and ffprobe must be available on PATH.")
    return ffmpeg, ffprobe


def parse_duration_tag(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        pass
    match = re.fullmatch(r"(\d+):(\d+):(\d+(?:\.\d+)?)", value)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def stream_duration(stream: dict[str, Any], fallback: float | None) -> float | None:
    direct = parse_duration_tag(stream.get("duration"))
    if direct is not None:
        return direct
    tags = stream.get("tags") or {}
    return parse_duration_tag(tags.get("DURATION")) or fallback


def probe_media(path: Path, ffprobe: str) -> dict[str, Any]:
    result = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,sample_rate,channels,channel_layout,start_time,duration:stream_tags=DURATION",
            "-of",
            "json",
            str(path),
        ]
    )
    if result.returncode != 0:
        raise AnalysisError(f"ffprobe failed: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    streams = data.get("streams") or []
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    if audio is None:
        raise AnalysisError("No audio stream was found.")
    format_duration = parse_duration_tag((data.get("format") or {}).get("duration"))
    return {
        "format": data.get("format") or {},
        "audio": audio,
        "video": video,
        "audio_duration": stream_duration(audio, format_duration),
        "video_duration": stream_duration(video, format_duration) if video else None,
        "audio_start": parse_duration_tag(audio.get("start_time")) or 0.0,
        "video_start": (parse_duration_tag(video.get("start_time")) or 0.0) if video else None,
    }


def parse_loudness(path: Path, ffmpeg: str) -> dict[str, float | None]:
    result = run_command(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            "ebur128=peak=true",
            "-f",
            "null",
            os.devnull,
        ]
    )
    text = result.stderr
    summary = text[text.rfind("Summary:") :] if "Summary:" in text else text
    integrated = re.search(r"I:\s*([+-]?(?:\d+(?:\.\d+)?|inf))\s+LUFS", summary)
    true_peak = re.search(r"Peak:\s*([+-]?(?:\d+(?:\.\d+)?|inf))\s+dBFS", summary)
    lra = re.search(r"LRA:\s*([+-]?(?:\d+(?:\.\d+)?|inf))\s+LU", summary)

    def value(match: re.Match[str] | None) -> float | None:
        if not match:
            return None
        try:
            parsed = float(match.group(1))
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None

    return {
        "integrated_lufs": value(integrated),
        "true_peak_dbtp": value(true_peak),
        "loudness_range_lu": value(lra),
    }


def read_exact(stream: Any, size: int) -> bytes:
    parts: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = stream.read(remaining)
        if not chunk:
            break
        parts.append(chunk)
        remaining -= len(chunk)
    return b"".join(parts)


def decoded_seconds(path: Path, ffmpeg: str) -> Iterable[np.ndarray]:
    command = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(path),
        "-map",
        "0:a:0",
        "-vn",
        "-ac",
        str(CHANNELS),
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "f32le",
        "pipe:1",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stdout is None or process.stderr is None:
        raise AnalysisError("Could not open ffmpeg output pipes.")
    while True:
        raw = read_exact(process.stdout, SECOND_BYTES)
        if not raw:
            break
        usable = len(raw) - len(raw) % (CHANNELS * FLOAT_BYTES)
        if usable:
            yield np.frombuffer(raw[:usable], dtype="<f4").reshape(-1, CHANNELS).astype(np.float64)
        if len(raw) < SECOND_BYTES:
            break
    stderr = process.stderr.read().decode("utf-8", errors="replace")
    return_code = process.wait()
    if return_code != 0:
        raise AnalysisError(f"ffmpeg decode failed: {stderr.strip()}")


def analyze_levels(path: Path, ffmpeg: str) -> dict[str, Any]:
    frame_db: list[float] = []
    second_db: list[float] = []
    channel_sum = np.zeros(CHANNELS)
    channel_square_sum = np.zeros(CHANNELS)
    cross_sum = 0.0
    channel_peak = np.zeros(CHANNELS)
    clipped = np.zeros(CHANNELS, dtype=np.int64)
    sample_count = 0

    for samples in decoded_seconds(path, ffmpeg):
        count = len(samples)
        sample_count += count
        channel_sum += samples.sum(axis=0)
        channel_square_sum += np.square(samples).sum(axis=0)
        cross_sum += float(np.sum(samples[:, 0] * samples[:, 1]))
        channel_peak = np.maximum(channel_peak, np.max(np.abs(samples), axis=0))
        clipped += np.sum(np.abs(samples) >= 0.999, axis=0)
        mono = samples.mean(axis=1)
        second_db.append(dbfs(float(np.sqrt(np.mean(np.square(mono))))))
        block_size = SAMPLE_RATE // 10
        for start in range(0, count, block_size):
            block = mono[start : start + block_size]
            if len(block) >= block_size // 2:
                frame_db.append(dbfs(float(np.sqrt(np.mean(np.square(block))))))

    if sample_count == 0 or not frame_db:
        raise AnalysisError("The audio stream decoded to zero samples.")

    frames = np.asarray(frame_db)
    digital_silence_fraction = float(np.mean(frames < -90.0))
    floor_frames = frames
    if digital_silence_fraction >= 0.05 and np.any(frames > -80.0):
        floor_frames = frames[frames > -80.0]
    p20 = float(np.percentile(floor_frames, 20))
    p30 = float(np.percentile(floor_frames, 30))
    p90 = float(np.percentile(floor_frames, 90))
    quiet = floor_frames[floor_frames <= p30]
    quiet_floor = float(np.median(quiet))
    active = frames[frames >= quiet_floor + 10.0]
    if len(active) < max(3, int(len(frames) * 0.05)):
        active = frames[frames >= np.percentile(frames, 70)]
    active_median = float(np.median(active))
    dynamic_range = p90 - p20
    quiet_seconds = len(quiet) / 10.0
    noise_reliable = quiet_seconds >= 1.0 and dynamic_range >= 8.0 and digital_silence_fraction < 0.05

    means = channel_sum / sample_count
    variances = channel_square_sum / sample_count - np.square(means)
    covariance = cross_sum / sample_count - means[0] * means[1]
    denominator = math.sqrt(max(variances[0] * variances[1], 1e-30))
    correlation = covariance / denominator

    return {
        "duration_decoded_seconds": sample_count / SAMPLE_RATE,
        "sample_peak_dbfs": [dbfs(value) for value in channel_peak],
        "clipped_samples": [int(value) for value in clipped],
        "channel_rms_dbfs": [power_db(value / sample_count) for value in channel_square_sum],
        "channel_correlation": float(correlation),
        "quiet_floor_dbfs": quiet_floor,
        "active_speech_rms_dbfs": active_median,
        "estimated_snr_db": active_median - quiet_floor,
        "dynamic_range_db": dynamic_range,
        "quiet_seconds": quiet_seconds,
        "digital_silence_fraction": digital_silence_fraction,
        "noise_measurement_reliable": noise_reliable,
        "second_rms_dbfs": second_db,
    }


def select_separated_peaks(db_spectrum: np.ndarray, search_indices: np.ndarray) -> list[int]:
    if len(search_indices) < 3:
        return []
    values = db_spectrum[search_indices]
    local = np.where((values[1:-1] > values[:-2]) & (values[1:-1] >= values[2:]))[0] + 1
    ordered = sorted((int(search_indices[index]) for index in local), key=lambda index: db_spectrum[index], reverse=True)
    selected: list[int] = []
    minimum_bins = int(30 / (SAMPLE_RATE / 65_536))
    for index in ordered:
        if all(abs(index - prior) >= minimum_bins for prior in selected):
            selected.append(index)
        if len(selected) >= 8:
            break
    return selected


def tone_measurement(psd: np.ndarray, frequencies: np.ndarray, frequency: float, radius: float) -> float:
    resolution = frequencies[1] - frequencies[0]
    mask = (frequencies >= frequency - radius) & (frequencies <= frequency + radius)
    return power_db(float(np.sum(psd[mask]) * resolution))


def analyze_spectrum(path: Path, ffmpeg: str, levels: dict[str, Any]) -> dict[str, Any]:
    nfft = 65_536
    frequencies = np.fft.rfftfreq(nfft, 1 / SAMPLE_RATE)
    search = np.flatnonzero((frequencies >= 2_000) & (frequencies <= 18_000))
    window = np.hanning(SAMPLE_RATE)
    scale = SAMPLE_RATE * float(np.sum(np.square(window)))
    groups: dict[tuple[int, int], list[dict[str, float]]] = defaultdict(list)
    hum: dict[int, list[dict[str, float]]] = defaultdict(list)
    second_levels = levels["second_rms_dbfs"]
    quiet_limit = levels["quiet_floor_dbfs"] + 4.0
    analyzed_seconds = 0

    for second_index, samples in enumerate(decoded_seconds(path, ffmpeg)):
        if len(samples) < SAMPLE_RATE:
            continue
        analyzed_seconds += 1
        for channel in range(CHANNELS):
            signal = samples[:SAMPLE_RATE, channel]
            signal = signal - float(np.mean(signal))
            spectrum = np.fft.rfft(signal * window, nfft)
            psd = 2.0 * np.square(np.abs(spectrum)) / scale
            db_spectrum = 10.0 * np.log10(psd + 1e-30)
            for index in select_separated_peaks(db_spectrum, search):
                frequency = float(frequencies[index])
                local_mask = (
                    (frequencies >= frequency - 250)
                    & (frequencies <= frequency + 250)
                    & ~((frequencies >= frequency - 15) & (frequencies <= frequency + 15))
                )
                prominence = float(db_spectrum[index] - np.median(db_spectrum[local_mask]))
                tone_db = tone_measurement(psd, frequencies, frequency, 5.0)
                if prominence >= 10.0 and tone_db >= -90.0:
                    key = (channel, int(round(frequency / 10.0) * 10))
                    groups[key].append(
                        {
                            "second": float(second_index),
                            "frequency": frequency,
                            "prominence_db": prominence,
                            "tone_rms_dbfs": tone_db,
                        }
                    )

            if second_index < len(second_levels) and second_levels[second_index] <= quiet_limit:
                for hum_frequency in (50, 60, 100, 120, 150, 180):
                    center = int(np.argmin(np.abs(frequencies - hum_frequency)))
                    local_mask = (
                        (frequencies >= hum_frequency - 20)
                        & (frequencies <= hum_frequency + 20)
                        & ~((frequencies >= hum_frequency - 3) & (frequencies <= hum_frequency + 3))
                    )
                    prominence = float(db_spectrum[center] - np.median(db_spectrum[local_mask]))
                    hum[hum_frequency].append(
                        {
                            "prominence_db": prominence,
                            "tone_rms_dbfs": tone_measurement(psd, frequencies, hum_frequency, 3.0),
                        }
                    )

    tone_groups: list[dict[str, Any]] = []
    for (channel, rounded_frequency), records in groups.items():
        tone_groups.append(
            {
                "channel": channel + 1,
                "frequency_hz": rounded_frequency,
                "count_seconds": len(records),
                "occurrence_ratio": len(records) / max(analyzed_seconds, 1),
                "median_prominence_db": float(np.median([item["prominence_db"] for item in records])),
                "max_prominence_db": max(item["prominence_db"] for item in records),
                "median_tone_rms_dbfs": float(np.median([item["tone_rms_dbfs"] for item in records])),
                "max_tone_rms_dbfs": max(item["tone_rms_dbfs"] for item in records),
                "first_timestamp_seconds": min(item["second"] for item in records),
            }
        )
    tone_groups.sort(key=lambda item: (item["count_seconds"], item["max_prominence_db"]), reverse=True)

    hum_summary: list[dict[str, float]] = []
    for frequency, records in hum.items():
        if records:
            hum_summary.append(
                {
                    "frequency_hz": float(frequency),
                    "median_prominence_db": float(np.median([item["prominence_db"] for item in records])),
                    "median_tone_rms_dbfs": float(np.median([item["tone_rms_dbfs"] for item in records])),
                    "sampled_seconds": float(len(records) / CHANNELS),
                }
            )

    return {
        "analyzed_seconds": analyzed_seconds,
        "tone_groups": tone_groups[:30],
        "hum": hum_summary,
    }


def add_range_finding(
    findings: list[Finding],
    value: float | None,
    code: str,
    label: str,
    warn_low: float | None,
    warn_high: float | None,
    fail_low: float | None,
    fail_high: float | None,
    unit: str,
) -> None:
    if value is None:
        findings.append(Finding("WARN", f"{code}_UNAVAILABLE", f"Could not measure {label}."))
        return
    if fail_low is not None and value < fail_low:
        findings.append(Finding("FAIL", f"{code}_LOW", f"{label} is too low: {value:.1f} {unit}."))
    elif fail_high is not None and value > fail_high:
        findings.append(Finding("FAIL", f"{code}_HIGH", f"{label} is too high: {value:.1f} {unit}."))
    elif warn_low is not None and value < warn_low:
        findings.append(Finding("WARN", f"{code}_LOW", f"{label} is below target: {value:.1f} {unit}."))
    elif warn_high is not None and value > warn_high:
        findings.append(Finding("WARN", f"{code}_HIGH", f"{label} is above target: {value:.1f} {unit}."))


def assess(
    profile_name: str,
    probe: dict[str, Any],
    loudness: dict[str, float | None],
    levels: dict[str, Any],
    spectrum: dict[str, Any],
) -> list[Finding]:
    profile = PROFILES[profile_name]
    findings: list[Finding] = []

    if sum(levels["clipped_samples"]) > 0:
        findings.append(Finding("FAIL", "CLIPPING", f"Detected {sum(levels['clipped_samples'])} clipped samples."))

    add_range_finding(
        findings,
        loudness["true_peak_dbtp"],
        "TRUE_PEAK",
        "True peak",
        profile["true_peak_warn_low"],
        profile["true_peak_warn_high"],
        profile["true_peak_fail_low"],
        profile["true_peak_fail_high"],
        "dBTP",
    )
    if profile["lufs_fail_low"] is not None:
        add_range_finding(
            findings,
            loudness["integrated_lufs"],
            "LOUDNESS",
            "Integrated loudness",
            profile["lufs_warn_low"],
            profile["lufs_warn_high"],
            profile["lufs_fail_low"],
            profile["lufs_fail_high"],
            "LUFS",
        )

    if profile["active_rms_low"] is not None:
        add_range_finding(
            findings,
            levels["active_speech_rms_dbfs"],
            "ACTIVE_RMS",
            "Active speech RMS",
            profile["active_rms_low"],
            profile["active_rms_high"],
            None,
            None,
            "dBFS",
        )

    if levels["noise_measurement_reliable"]:
        noise_floor = levels["quiet_floor_dbfs"]
        if noise_floor > float(profile["noise_fail_above"]):
            findings.append(Finding("FAIL", "NOISE_FLOOR", f"Noise floor is too high: {noise_floor:.1f} dBFS."))
        elif noise_floor > float(profile["noise_warn_above"]):
            findings.append(Finding("WARN", "NOISE_FLOOR", f"Noise floor is above target: {noise_floor:.1f} dBFS."))

        snr = levels["estimated_snr_db"]
        if snr < float(profile["snr_fail_below"]):
            findings.append(Finding("FAIL", "LOW_SNR", f"Estimated speech-to-noise ratio is too low: {snr:.1f} dB."))
        elif snr < float(profile["snr_warn_below"]):
            findings.append(Finding("WARN", "LOW_SNR", f"Estimated speech-to-noise ratio is below target: {snr:.1f} dB."))
    elif bool(profile["require_noise_measurement"]):
        findings.append(Finding("FAIL", "NOISE_UNVERIFIED", "Not enough clean pauses to verify the noise floor."))
    else:
        findings.append(Finding("INFO", "NOISE_UNVERIFIED", "Continuous program audio prevented a reliable final-mix noise-floor estimate."))

    recurrence = max(3, math.ceil(max(spectrum["analyzed_seconds"], 1) * 0.02))
    for tone in spectrum["tone_groups"]:
        fixed_high = (
            tone["frequency_hz"] >= 5_000
            and tone["count_seconds"] >= recurrence
            and tone["median_prominence_db"] >= 18.0
            and tone["median_tone_rms_dbfs"] >= -68.0
        )
        severe_squeal = (
            tone["count_seconds"] >= 3
            and tone["max_prominence_db"] >= 30.0
            and tone["max_tone_rms_dbfs"] >= -50.0
        )
        suspicious = (
            tone["frequency_hz"] >= 5_000
            and tone["count_seconds"] >= recurrence
            and tone["median_prominence_db"] >= 15.0
            and tone["median_tone_rms_dbfs"] >= -78.0
        )
        if fixed_high or severe_squeal:
            findings.append(
                Finding(
                    "FAIL",
                    "FIXED_TONE",
                    f"Persistent narrow tone near {tone['frequency_hz']:.0f} Hz on channel {tone['channel']}.",
                    tone["first_timestamp_seconds"],
                )
            )
        elif suspicious:
            findings.append(
                Finding(
                    "WARN",
                    "SUSPECT_TONE",
                    f"Review a possible narrow tone near {tone['frequency_hz']:.0f} Hz on channel {tone['channel']}.",
                    tone["first_timestamp_seconds"],
                )
            )

    for hum in spectrum["hum"]:
        if hum["sampled_seconds"] >= 1 and hum["median_prominence_db"] >= 15 and hum["median_tone_rms_dbfs"] >= -55:
            findings.append(
                Finding(
                    "FAIL",
                    "MAINS_HUM",
                    f"Audible mains-related tone near {hum['frequency_hz']:.0f} Hz was detected in quiet sections.",
                )
            )
        elif hum["sampled_seconds"] >= 1 and hum["median_prominence_db"] >= 12 and hum["median_tone_rms_dbfs"] >= -65:
            findings.append(
                Finding(
                    "WARN",
                    "MAINS_HUM",
                    f"Review a weak mains-related tone near {hum['frequency_hz']:.0f} Hz.",
                )
            )

    peaks = levels["sample_peak_dbfs"]
    if abs(peaks[0] - peaks[1]) > 10:
        findings.append(Finding("FAIL", "CHANNEL_IMBALANCE", f"Left-right peak difference is {abs(peaks[0] - peaks[1]):.1f} dB."))
    elif abs(peaks[0] - peaks[1]) > 3:
        findings.append(Finding("WARN", "CHANNEL_IMBALANCE", f"Left-right peak difference is {abs(peaks[0] - peaks[1]):.1f} dB."))
    if levels["channel_correlation"] < -0.2:
        findings.append(Finding("FAIL", "PHASE", f"Channel correlation indicates possible phase inversion: {levels['channel_correlation']:.2f}."))

    if probe["video"] is not None:
        audio_duration = probe["audio_duration"]
        video_duration = probe["video_duration"]
        if audio_duration is not None and video_duration is not None:
            difference = abs(audio_duration - video_duration)
            if difference > 0.25:
                findings.append(Finding("FAIL", "DURATION_MISMATCH", f"Audio-video duration difference is {difference * 1000:.0f} ms."))
            elif difference > 0.10:
                findings.append(Finding("WARN", "DURATION_MISMATCH", f"Audio-video duration difference is {difference * 1000:.0f} ms."))
        start_difference = abs(float(probe["audio_start"]) - float(probe["video_start"]))
        if start_difference > 0.10:
            findings.append(Finding("FAIL", "START_MISMATCH", f"Audio-video start difference is {start_difference * 1000:.0f} ms."))

    return findings


def build_report(path: Path, profile: str) -> dict[str, Any]:
    ffmpeg, ffprobe = require_tools()
    probe = probe_media(path, ffprobe)
    loudness = parse_loudness(path, ffmpeg)
    levels = analyze_levels(path, ffmpeg)
    spectrum = analyze_spectrum(path, ffmpeg, levels)
    findings = assess(profile, probe, loudness, levels, spectrum)
    return {
        "file": str(path.resolve()),
        "profile": profile,
        "probe": probe,
        "loudness": loudness,
        "levels": {key: value for key, value in levels.items() if key != "second_rms_dbfs"},
        "spectrum": spectrum,
        "findings": [asdict(finding) for finding in findings],
    }


def status_for(report: dict[str, Any], strict: bool) -> str:
    severities = {finding["severity"] for finding in report["findings"]}
    if "FAIL" in severities or (strict and "WARN" in severities):
        return "FAIL"
    if "WARN" in severities:
        return "WARN"
    return "PASS"


def print_text_report(report: dict[str, Any]) -> None:
    print(f"AUDIO QC: {report['status']}")
    print(f"File: {report['file']}")
    print(f"Profile: {report['profile']}")
    for finding in report["findings"]:
        timestamp = ""
        if finding["timestamp_seconds"] is not None:
            minutes, seconds = divmod(int(finding["timestamp_seconds"]), 60)
            timestamp = f" at {minutes:02d}:{seconds:02d}"
        print(f"{finding['severity']}: {finding['code']}: {finding['message']}{timestamp}")
    loudness = report["loudness"]
    levels = report["levels"]
    print("Metrics:")
    print(f"  Integrated loudness: {loudness['integrated_lufs']} LUFS")
    print(f"  True peak: {loudness['true_peak_dbtp']} dBTP")
    print(f"  Quiet floor: {levels['quiet_floor_dbfs']:.1f} dBFS")
    print(f"  Estimated SNR: {levels['estimated_snr_db']:.1f} dB")
    print(f"  Channel peaks: {levels['sample_peak_dbfs'][0]:.1f}, {levels['sample_peak_dbfs'][1]:.1f} dBFS")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path, help="Audio or video file to inspect.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="final")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of the text report.")
    parser.add_argument("--report-json", type=Path, help="Write the complete report to this path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.media.is_file():
        print(f"Audio QC error: file not found: {args.media}", file=sys.stderr)
        return 2
    try:
        report = build_report(args.media, args.profile)
    except (AnalysisError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Audio QC error: {exc}", file=sys.stderr)
        return 2
    report["strict"] = bool(args.strict)
    report["status"] = status_for(report, args.strict)
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
