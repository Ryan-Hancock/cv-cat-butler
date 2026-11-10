import numpy as np

from cat_butler.detector import Box
from cat_butler.pipeline import watch
from cat_butler.trigger import DoorbellTrigger, TriggerConfig
from cat_butler.zone import Zone

FRAME = np.zeros((100, 100, 3), dtype=np.uint8)
ON_MAT = Box(40, 40, 60, 90)
OFF_MAT = Box(40, 5, 60, 20)
CONFIG = TriggerConfig(dwell_seconds=1.0, grace_seconds=0.5, cooldown_seconds=60.0)
MAT = Zone(0.0, 0.5, 1.0, 1.0)


def frames(count, fps=10):
    return [(i / fps, FRAME) for i in range(count)]


def run(detect, count=30, interval=0.2, on_frame=None):
    rung = []
    total = watch(
        frames(count),
        detect,
        MAT,
        DoorbellTrigger(CONFIG),
        lambda: rung.append(True),
        interval=interval,
        on_frame=on_frame,
    )
    assert total == len(rung)
    return total


def test_cat_waiting_on_the_mat_rings_once():
    assert run(lambda frame: [ON_MAT]) == 1


def test_cat_outside_the_zone_does_not_ring():
    assert run(lambda frame: [OFF_MAT]) == 0


def test_no_cats_does_not_ring():
    assert run(lambda frame: []) == 0


def test_detection_only_runs_at_the_requested_interval():
    calls = []

    def detect(frame):
        calls.append(True)
        return []

    run(detect, count=30, interval=1.0)
    assert len(calls) == 3


def test_on_frame_returning_false_stops_the_loop():
    seen = []

    def stop_after_five(frame, cats, state):
        seen.append(True)
        return len(seen) < 5

    run(lambda frame: [], on_frame=stop_after_five)
    assert len(seen) == 5
