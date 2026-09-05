class VoiceSelectionError(Exception):
    """Raised when a suitable voice cannot be selected."""


class VoiceSelector:

    VOICES = {
        "ta": {
            "male": "ta-IN-ValluvarNeural",
            "female": "ta-IN-PallaviNeural",
        },
        "en": {
            "male": "en-US-AndrewNeural",
            "female": "en-US-AvaNeural",
        },
    }

    def detect_language(self, text: str) -> str:
        if not text or not text.strip():
            raise ValueError(
                "Narration cannot be empty."
            )

        tamil_characters = 0
        english_characters = 0

        for char in text:
            if "\u0B80" <= char <= "\u0BFF":
                tamil_characters += 1
            elif char.isalpha() and char.isascii():
                english_characters += 1

        if (
            tamil_characters == 0
            and english_characters == 0
        ):
            raise VoiceSelectionError(
                "Unable to detect narration language."
            )

        if tamil_characters > english_characters:
            return "ta"

        return "en"

    def select_voice(
        self,
        narration: str,
        gender: str | None,
    ) -> str:

        # If no voice is provided, use male as the default.
        if gender is None:
            gender = "male"

        gender = gender.lower().strip()

        if gender not in {"male", "female"}:
            raise ValueError(
                "Voice must be either 'male' or 'female'."
            )

        language = self.detect_language(
            narration
        )

        return self.VOICES[language][gender]