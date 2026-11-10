from cat_butler.trigger import DoorbellTrigger, State, TriggerConfig

CONFIG = TriggerConfig(dwell_seconds=3.0, grace_seconds=1.0, cooldown_seconds=60.0)


def feed(trigger, observations):
    """Feed (time, cat_at_door) pairs and return the times the bell rang."""
    return [now for now, seen in observations if trigger.update(seen, now)]


def test_empty_doorstep_never_rings():
    trigger = DoorbellTrigger(CONFIG)
    assert feed(trigger, [(t, False) for t in range(10)]) == []
    assert trigger.state is State.IDLE


def test_cat_walking_past_does_not_ring():
    trigger = DoorbellTrigger(CONFIG)
    assert feed(trigger, [(0, True), (1, True), (2, True), (3.5, False), (4, False)]) == []
    assert trigger.state is State.IDLE


def test_waiting_cat_rings_once_dwell_is_reached():
    trigger = DoorbellTrigger(CONFIG)
    assert feed(trigger, [(t, True) for t in range(5)]) == [3]


def test_brief_missed_detection_does_not_reset_dwell():
    trigger = DoorbellTrigger(CONFIG)
    observations = [(0, True), (1, True), (1.5, False), (2, True), (3, True)]
    assert feed(trigger, observations) == [3]


def test_cat_leaving_longer_than_grace_restarts_dwell():
    trigger = DoorbellTrigger(CONFIG)
    observations = [(0, True), (1, True), (2.5, False), (3, True), (5, True), (6, True)]
    assert feed(trigger, observations) == [6]


def test_cooldown_prevents_repeat_rings():
    trigger = DoorbellTrigger(CONFIG)
    assert feed(trigger, [(t, True) for t in range(0, 40)]) == [3]
    assert trigger.state is State.COOLDOWN


def test_cat_still_waiting_after_cooldown_rings_again():
    trigger = DoorbellTrigger(CONFIG)
    assert feed(trigger, [(t, True) for t in range(0, 70)]) == [3, 66]
