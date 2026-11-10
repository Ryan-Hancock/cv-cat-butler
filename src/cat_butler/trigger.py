"""Decides when a detected cat counts as a cat that wants to come in.

A detector answers "is there a cat in this frame?". The doorbell needs a
different answer: "has a cat been waiting here for a while?". This module turns
the first into the second, and knows nothing about cameras or models.
"""

from dataclasses import dataclass
from enum import Enum


class State(Enum):
    IDLE = "idle"
    WATCHING = "watching"
    COOLDOWN = "cooldown"


@dataclass(frozen=True)
class TriggerConfig:
    dwell_seconds: float = 3.0
    """How long a cat must stay at the door before the bell rings."""

    grace_seconds: float = 1.5
    """How long the cat may go undetected before we decide it has left.

    Detectors miss the odd frame, especially when a cat turns or grooms. Without
    this, one missed frame would restart the dwell timer.
    """

    cooldown_seconds: float = 60.0
    """Minimum time between rings, so a patient cat doesn't ring constantly."""


class DoorbellTrigger:
    def __init__(self, config: TriggerConfig = TriggerConfig()):
        self.config = config
        self.state = State.IDLE
        self._arrived_at = 0.0
        self._last_seen = 0.0
        self._rang_at = 0.0

    def update(self, cat_at_door: bool, now: float) -> bool:
        """Record one observation. Returns True when the bell should ring."""
        if self.state is State.COOLDOWN:
            if now - self._rang_at < self.config.cooldown_seconds:
                return False
            self.state = State.IDLE

        if self.state is State.IDLE:
            if not cat_at_door:
                return False
            self.state = State.WATCHING
            self._arrived_at = now
            self._last_seen = now

        if cat_at_door:
            self._last_seen = now
            if now - self._arrived_at >= self.config.dwell_seconds:
                self.state = State.COOLDOWN
                self._rang_at = now
                return True
        elif now - self._last_seen > self.config.grace_seconds:
            self.state = State.IDLE

        return False
