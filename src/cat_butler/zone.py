"""The part of the camera image that counts as "at the door"."""

from dataclasses import dataclass

from cat_butler.detector import Box


@dataclass(frozen=True)
class Zone:
    """A rectangle in fractions of the frame, so it survives resolution changes."""

    x1: float = 0.0
    y1: float = 0.0
    x2: float = 1.0
    y2: float = 1.0

    def __post_init__(self):
        if not (0 <= self.x1 < self.x2 <= 1 and 0 <= self.y1 < self.y2 <= 1):
            raise ValueError(
                "zone must satisfy 0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1, "
                f"got {self.x1},{self.y1},{self.x2},{self.y2}"
            )

    @classmethod
    def parse(cls, text: str) -> "Zone":
        """Build a zone from "x1,y1,x2,y2"."""
        parts = text.split(",")
        if len(parts) != 4:
            raise ValueError(f'zone must be "x1,y1,x2,y2", got "{text}"')
        return cls(*(float(part) for part in parts))

    def contains(self, box: Box, frame_width: int, frame_height: int) -> bool:
        """True if the bottom-centre of the box is inside the zone.

        The bottom edge is roughly where the paws are. Using it instead of the
        box centre means a cat on the path behind the doormat doesn't count just
        because it looks like it overlaps the mat in the image.
        """
        x = (box.x1 + box.x2) / 2 / frame_width
        y = box.y2 / frame_height
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def to_pixels(self, frame_width: int, frame_height: int) -> tuple[int, int, int, int]:
        return (
            int(self.x1 * frame_width),
            int(self.y1 * frame_height),
            int(self.x2 * frame_width),
            int(self.y2 * frame_height),
        )
