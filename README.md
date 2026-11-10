# Cat Butler

A camera watches the door. When a cat sits there long enough to mean it, a doorbell rings.

Spotting a cat is the easy part, because a pretrained model already does it. The interesting part is telling a cat that **wants to come in** from a cat that's just walking past.

## How it works

```
camera -> YOLO finds cats -> is one in the door zone? -> has it stayed there? -> ding dong
```

| Step | File | What it does |
|---|---|---|
| Detect | [detector.py](src/cat_butler/detector.py) | Runs YOLO11n, pretrained on COCO, keeping only the `cat` class |
| Locate | [zone.py](src/cat_butler/zone.py) | Checks whether the cat's paws (the bottom-centre of its box) are in the door area |
| Decide | [trigger.py](src/cat_butler/trigger.py) | A small state machine that turns "cat in this frame" into "cat waiting" |
| Ring | [doorbell.py](src/cat_butler/doorbell.py) | Synthesises a ding-dong and plays it, with no audio libraries or sound files |

The decision comes from three timers:

| Timer | Default | Why it exists |
|---|---|---|
| Dwell | 3 s | A cat has to stay this long, so passing cats don't ring |
| Grace | 1.5 s | Detectors miss the odd frame, and one miss shouldn't restart the wait |
| Cooldown | 60 s | One ring per request. A cat still waiting afterwards rings again |

```
          cat at door                dwell reached
  IDLE ---------------> WATCHING ---------------> COOLDOWN (ding dong)
   ^                       |                         |
   |   gone > grace        |                         |
   +-----------------------+                         |
   +-------------------- cooldown over --------------+
```

## Setup

You need [uv](https://docs.astral.sh/uv/) and a camera. The first run downloads the model weights (about 5 MB).

```sh
git clone <this repo>
cd cv-cat-butler
uv sync
```

**On Windows, run it natively rather than in WSL.** WSL can't see USB webcams by default. An IP camera stream works from either.

## Usage

```sh
# Default webcam, with a window showing what the model sees
uv run cat-butler --preview

# Only count cats on the doormat (left, top, right, bottom as fractions of the frame)
uv run cat-butler --preview --zone 0.2,0.6,0.8,1.0

# An IP camera, with no window
uv run cat-butler --source rtsp://user:password@192.168.1.50/stream

# Test on a recording without making any noise
uv run cat-butler --source my_cat.mp4 --silent
```

Set up the zone with `--preview` on: the green rectangle is the door area, and a cat counts once the bottom-middle of its orange box is inside it.

Run `uv run cat-butler --help` for every option, including `--sound my_bell.wav` for your own chime.

## Tuning

| Problem | Try |
|---|---|
| Rings when the cat walks past | Raise `--dwell`, or tighten `--zone` |
| Slow to notice the cat | Lower `--confidence`, or move the camera closer |
| Rings for shadows or the neighbour's dog | Raise `--confidence` |
| Keeps forgetting a cat that's sitting still | Raise `--grace` |
| Uses too much CPU | Raise `--interval` |

## Tests

```sh
uv run pytest
```

The tests cover the zone, the timers and the loop with a fake detector, so they need no camera or model.

## Licence note

[Ultralytics YOLO](https://github.com/ultralytics/ultralytics) is licensed under AGPL-3.0, which matters if you build on this commercially.
