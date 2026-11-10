import pytest

from cat_butler.detector import Box
from cat_butler.zone import Zone


def test_parse_reads_fractions():
    assert Zone.parse("0.1,0.2,0.8,1") == Zone(0.1, 0.2, 0.8, 1.0)


@pytest.mark.parametrize("text", ["0.1,0.2,0.8", "0.8,0,0.1,1", "0,0,1.5,1", "a,b,c,d"])
def test_parse_rejects_bad_zones(text):
    with pytest.raises(ValueError):
        Zone.parse(text)


def test_contains_uses_the_bottom_centre_of_the_box():
    doormat = Zone(0.25, 0.5, 0.75, 1.0)
    assert doormat.contains(Box(40, 10, 60, 70), 100, 100)
    # The box overlaps the mat, but its paws are above it.
    assert not doormat.contains(Box(40, 10, 60, 45), 100, 100)
    # Paws are level with the mat, but to one side of it.
    assert not doormat.contains(Box(0, 40, 20, 70), 100, 100)


def test_to_pixels_scales_to_the_frame():
    assert Zone(0.25, 0.5, 0.75, 1.0).to_pixels(200, 100) == (50, 50, 150, 100)
