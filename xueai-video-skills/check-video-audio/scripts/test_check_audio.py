#!/usr/bin/env python3
"""Unit tests for the audio QC policy layer."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("check_audio.py")
SPEC = importlib.util.spec_from_file_location("check_audio", SCRIPT)
assert SPEC and SPEC.loader
CHECK_AUDIO = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECK_AUDIO
SPEC.loader.exec_module(CHECK_AUDIO)


def base_probe() -> dict:
    return {
        "audio": {},
        "video": {},
        "audio_duration": 10.0,
        "video_duration": 10.04,
        "audio_start": 0.0,
        "video_start": 0.0,
    }


def base_levels() -> dict:
    return {
        "clipped_samples": [0, 0],
        "quiet_floor_dbfs": -60.0,
        "active_speech_rms_dbfs": -22.0,
        "estimated_snr_db": 38.0,
        "noise_measurement_reliable": True,
        "sample_peak_dbfs": [-2.0, -2.1],
        "channel_correlation": 0.99,
    }


class PolicyTests(unittest.TestCase):
    def test_clean_final_passes(self) -> None:
        findings = CHECK_AUDIO.assess(
            "final",
            base_probe(),
            {"integrated_lufs": -16.0, "true_peak_dbtp": -1.7, "loudness_range_lu": 6.0},
            base_levels(),
            {"analyzed_seconds": 10, "tone_groups": [], "hum": []},
        )
        self.assertFalse([finding for finding in findings if finding.severity in {"FAIL", "WARN"}])

    def test_bottom_noise_fails(self) -> None:
        levels = base_levels()
        levels["quiet_floor_dbfs"] = -43.0
        levels["estimated_snr_db"] = 20.0
        findings = CHECK_AUDIO.assess(
            "narration",
            base_probe(),
            {"integrated_lufs": -16.0, "true_peak_dbtp": -1.7, "loudness_range_lu": 6.0},
            levels,
            {"analyzed_seconds": 10, "tone_groups": [], "hum": []},
        )
        self.assertIn("NOISE_FLOOR", {finding.code for finding in findings if finding.severity == "FAIL"})

    def test_persistent_10khz_tone_fails(self) -> None:
        tone = {
            "channel": 1,
            "frequency_hz": 10_000,
            "count_seconds": 5,
            "occurrence_ratio": 0.5,
            "median_prominence_db": 24.0,
            "max_prominence_db": 40.0,
            "median_tone_rms_dbfs": -55.0,
            "max_tone_rms_dbfs": -45.0,
            "first_timestamp_seconds": 2.0,
        }
        findings = CHECK_AUDIO.assess(
            "final",
            base_probe(),
            {"integrated_lufs": -16.0, "true_peak_dbtp": -1.7, "loudness_range_lu": 6.0},
            base_levels(),
            {"analyzed_seconds": 10, "tone_groups": [tone], "hum": []},
        )
        self.assertIn("FIXED_TONE", {finding.code for finding in findings if finding.severity == "FAIL"})

    def test_clipping_fails(self) -> None:
        levels = base_levels()
        levels["clipped_samples"] = [5, 0]
        findings = CHECK_AUDIO.assess(
            "final",
            base_probe(),
            {"integrated_lufs": -16.0, "true_peak_dbtp": -0.2, "loudness_range_lu": 6.0},
            levels,
            {"analyzed_seconds": 10, "tone_groups": [], "hum": []},
        )
        codes = {finding.code for finding in findings if finding.severity == "FAIL"}
        self.assertIn("CLIPPING", codes)
        self.assertIn("TRUE_PEAK_HIGH", codes)


if __name__ == "__main__":
    unittest.main()
