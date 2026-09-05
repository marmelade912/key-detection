"""Synthesize simple chords and check that Tonal_Fragment names the right key."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SPOTIPY_CLIENT_ID", "test")
os.environ.setdefault("SPOTIPY_CLIENT_SECRET", "test")

from app import Tonal_Fragment  # noqa: E402

SR = 22050


def _tone(freq, seconds=2.0, sr=SR):
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    # a few harmonics so the chroma is not a single needle
    return sum((0.6 ** k) * np.sin(2 * np.pi * freq * (k + 1) * t) for k in range(4))


def _chord(freqs):
    y = sum(_tone(f) for f in freqs)
    return (y / np.max(np.abs(y))).astype(np.float32)


@pytest.mark.parametrize(
    "freqs, expected",
    [
        ((261.63, 329.63, 392.00), "C major"),   # C E G
        ((220.00, 261.63, 329.63), "A minor"),   # A C E
        ((196.00, 246.94, 293.66), "G major"),   # G B D
    ],
)
def test_detects_triad_key(freqs, expected):
    fragment = Tonal_Fragment(_chord(freqs), SR)
    info = fragment.get_key_info()
    assert info["key"] == expected
    assert 0.0 < info["confidence"] <= 1.0


def test_alternative_key_is_never_the_best_key():
    fragment = Tonal_Fragment(_chord((261.63, 329.63, 392.00)), SR)
    info = fragment.get_key_info()
    assert info["alternative_key"] != info["key"]
