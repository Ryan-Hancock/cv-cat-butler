"""Synthesises a ding-dong and plays it without any audio dependencies."""

import logging
import math
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44_100
DING_HZ = 659.25  # E5
DONG_HZ = 523.25  # C5
DONG_STARTS_AT = 0.5
DURATION = 2.0
DECAY_RATE = 3.5
ATTACK_SECONDS = 0.005  # A short fade-in stops each note starting with a click
VOLUME = 0.8

# Tried in order on macOS and Linux. Windows uses winsound instead.
PLAYERS = (
    ["afplay"],
    ["paplay"],
    ["aplay", "-q"],
    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
)


def _chime(frequency: float, t: float) -> float:
    """One struck-chime note at t seconds after it starts, roughly in [-1, 1]."""
    if t < 0:
        return 0.0
    envelope = min(t / ATTACK_SECONDS, 1.0) * math.exp(-DECAY_RATE * t)
    fundamental = math.sin(2 * math.pi * frequency * t)
    overtone = 0.4 * math.sin(2 * math.pi * frequency * 2 * t)
    # Slightly inharmonic, which is what makes a chime sound metallic.
    shimmer = 0.2 * math.sin(2 * math.pi * frequency * 3.01 * t)
    return envelope * (fundamental + overtone + shimmer) / 1.6


def write_doorbell(path: Path) -> Path:
    """Write a two-note ding-dong to a 16-bit mono WAV file."""
    frames = bytearray()
    for i in range(int(SAMPLE_RATE * DURATION)):
        t = i / SAMPLE_RATE
        mixed = _chime(DING_HZ, t) + _chime(DONG_HZ, t - DONG_STARTS_AT)
        sample = max(-1.0, min(1.0, mixed * VOLUME))
        frames += struct.pack("<h", int(sample * 32767))

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(frames))
    return path


def play(path: Path) -> None:
    """Start playing a WAV file and return immediately, so detection keeps running."""
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        return

    for player in PLAYERS:
        if shutil.which(player[0]):
            subprocess.Popen(
                [*player, str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
    logger.warning("No audio player found. Install one of: %s", [p[0] for p in PLAYERS])
