"""Finds cats in a frame using a pretrained YOLO model."""

from dataclasses import dataclass

import numpy as np

COCO_CAT_CLASS = 15


@dataclass(frozen=True)
class Box:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = 1.0


class CatDetector:
    def __init__(self, model: str = "yolo11n.pt", confidence: float = 0.4):
        # Imported here because it pulls in PyTorch, which takes seconds to load
        # and isn't needed by anything else in the package.
        from ultralytics import YOLO

        self._model = YOLO(model)
        self._confidence = confidence

    def __call__(self, frame: np.ndarray) -> list[Box]:
        result = self._model.predict(
            frame,
            classes=[COCO_CAT_CLASS],
            conf=self._confidence,
            verbose=False,
        )[0]
        return [
            Box(*xyxy, confidence=confidence)
            for xyxy, confidence in zip(
                result.boxes.xyxy.tolist(), result.boxes.conf.tolist()
            )
        ]
