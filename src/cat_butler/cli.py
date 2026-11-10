"""Command-line entry point: opens the camera and runs the watch loop."""

import argparse
import logging
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np

from cat_butler.detector import Box, CatDetector
from cat_butler.doorbell import play, write_doorbell
from cat_butler.pipeline import watch
from cat_butler.trigger import DoorbellTrigger, State, TriggerConfig
from cat_butler.zone import Zone

logger = logging.getLogger("cat_butler")

WINDOW_TITLE = "Cat Butler (q to quit)"
GREEN = (0, 200, 0)
ORANGE = (0, 165, 255)
WHITE = (255, 255, 255)
FALLBACK_FPS = 30.0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cat-butler",
        description="Ring a doorbell when a cat is waiting at the door.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--source", default="0", help="webcam index, video file or stream URL")
    parser.add_argument(
        "--zone",
        type=Zone.parse,
        default=Zone(),
        metavar="X1,Y1,X2,Y2",
        help="door area as fractions of the frame",
    )
    parser.add_argument("--dwell", type=float, default=3.0, help="seconds a cat must wait")
    parser.add_argument("--grace", type=float, default=1.5, help="seconds of missed detections to tolerate")
    parser.add_argument("--cooldown", type=float, default=60.0, help="minimum seconds between rings")
    parser.add_argument("--interval", type=float, default=0.2, help="seconds between detections")
    parser.add_argument("--confidence", type=float, default=0.4, help="minimum detection confidence")
    parser.add_argument("--model", default="yolo11n.pt", help="YOLO weights, downloaded if missing")
    parser.add_argument("--sound", type=Path, help="WAV file to play instead of the built-in chime")
    parser.add_argument("--silent", action="store_true", help="log rings without playing a sound")
    parser.add_argument("--preview", action="store_true", help="show a window with the detections")
    return parser.parse_args(argv)


def read_frames(capture: cv2.VideoCapture, source: str) -> Iterator[tuple[float, np.ndarray]]:
    """Yield (seconds, frame). Files use video time so they replay realistically."""
    is_file = Path(source).is_file()
    fps = capture.get(cv2.CAP_PROP_FPS) or FALLBACK_FPS
    index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            return
        yield (index / fps if is_file else time.monotonic()), frame
        index += 1


def make_preview(zone: Zone):
    """Return an on_frame callback that draws the zone, cats and current state."""

    def show(frame: np.ndarray, cats: list[Box], state: State) -> bool:
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = zone.to_pixels(width, height)
        cv2.rectangle(frame, (x1, y1), (x2, y2), GREEN, 2)
        for cat in cats:
            top_left = (int(cat.x1), int(cat.y1))
            cv2.rectangle(frame, top_left, (int(cat.x2), int(cat.y2)), ORANGE, 2)
            label = f"cat {cat.confidence:.2f}"
            cv2.putText(frame, label, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.6, ORANGE, 2)
        cv2.putText(frame, state.value, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)
        cv2.imshow(WINDOW_TITLE, frame)
        return cv2.waitKey(1) & 0xFF != ord("q")

    return show


def make_ring(args: argparse.Namespace):
    if args.silent:
        return lambda: None
    path = args.sound or write_doorbell(Path(tempfile.gettempdir()) / "cat-butler-doorbell.wav")
    return lambda: play(path)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    source = int(args.source) if args.source.isdigit() else args.source
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        logger.error("Could not open video source: %s", args.source)
        return 1

    trigger = DoorbellTrigger(TriggerConfig(args.dwell, args.grace, args.cooldown))
    detector = CatDetector(args.model, args.confidence)
    logger.info("Watching %s. Press Ctrl+C to stop.", args.source)

    try:
        rings = watch(
            read_frames(capture, args.source),
            detector,
            args.zone,
            trigger,
            make_ring(args),
            interval=args.interval,
            on_frame=make_preview(args.zone) if args.preview else None,
        )
        logger.info("Finished. The bell rang %d time(s).", rings)
    except KeyboardInterrupt:
        logger.info("Stopped.")
    finally:
        capture.release()
        if args.preview:
            cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
