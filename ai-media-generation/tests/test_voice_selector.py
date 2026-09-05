import pytest

from app.services.voice_selector import VoiceSelector


def test_tamil_male_voice():
    selector = VoiceSelector()

    voice = selector.select_voice(
        narration="விவசாயி தனது வயலில் வேலை செய்கிறார்.",
        gender="male",
    )

    assert voice == "ta-IN-ValluvarNeural"


def test_tamil_female_voice():
    selector = VoiceSelector()

    voice = selector.select_voice(
        narration="விவசாயி தனது வயலில் வேலை செய்கிறார்.",
        gender="female",
    )

    assert voice == "ta-IN-PallaviNeural"


def test_english_male_voice():
    selector = VoiceSelector()

    voice = selector.select_voice(
        narration="A farmer is working in his field.",
        gender="male",
    )

    assert voice == "en-US-AndrewNeural"


def test_english_female_voice():
    selector = VoiceSelector()

    voice = selector.select_voice(
        narration="A farmer is working in his field.",
        gender="female",
    )

    assert voice == "en-US-AvaNeural"


def test_none_voice_uses_default_male():
    selector = VoiceSelector()

    voice = selector.select_voice(
        narration="A farmer is working in his field.",
        gender=None,
    )

    assert voice == "en-US-AndrewNeural"


def test_invalid_voice_rejected():
    selector = VoiceSelector()

    with pytest.raises(ValueError):
        selector.select_voice(
            narration="A farmer is working in his field.",
            gender="unknown",
        )


def test_empty_narration_rejected():
    selector = VoiceSelector()

    with pytest.raises(ValueError):
        selector.select_voice(
            narration="",
            gender="male",
        )