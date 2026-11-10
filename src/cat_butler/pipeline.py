"""Connects frames, detector, zone and trigger into one loop."""

import logging
from collections.abc import Callable, Iterable

import numpy as np

from cat_butler.detector import Box
from cat_butler.trigger import DoorbellTrigger, State
from cat_butler.zone import Zone

logger = logging.getLogger(__name__)

Detect = Callable[[np.ndarray], list[Box]]
OnFrame = Callable[[np.ndarray, list[Box], State], bool]


def watch(
    frames: Iterable[tuple[float, np.ndarray]],
    detect: Detect,
    zone: Zone,
    trigger: DoorbellTrigger,
    ring: Callable[[], None],
    interval: float = 0.2,
    on_frame: OnFrame | None = None,
) -> int:
    """Run until the frames end or on_frame returns False. Returns the ring count.

    Each frame comes with its timestamp in seconds. Every frame is still consumed
    between detections, because a live camera buffers whatever we don't read and
    we would drift further and further behind real time.
    """
    rings = 0
    next_detection = float("-inf")
    cats: list[Box] = []

    for now, frame in frames:
        if now >= next_detection:
            next_detection = now + interval
            height, width = frame.shape[:2]
            cats = detect(frame)
            at_door = any(zone.contains(cat, width, height) for cat in cats)

            previous = trigger.state
            should_ring = trigger.update(at_door, now)
            if trigger.state is not previous:
                logger.info("%7.2fs  %s -> %s", now, previous.value, trigger.state.value)
            if should_ring:
                logger.info("%7.2fs  Ding dong! The cat wants to come in.", now)
                ring()
                rings += 1

        if on_frame is not None and not on_frame(frame, cats, trigger.state):
            break

    return rings
