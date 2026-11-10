import wave

from cat_butler.doorbell import DURATION, SAMPLE_RATE, write_doorbell


def test_write_doorbell_produces_a_non_silent_wav(tmp_path):
    path = write_doorbell(tmp_path / "bell.wav")

    with wave.open(str(path)) as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == SAMPLE_RATE
        assert wav.getnframes() == int(SAMPLE_RATE * DURATION)
        assert any(wav.readframes(wav.getnframes()))
