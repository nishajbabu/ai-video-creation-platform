import re


class SceneSplitterError(Exception):
    """Raised when a script cannot be split into scenes."""


class SceneSplitter:

    def split(
        self,
        script: str,
    ) -> list[str]:

        if not script or not script.strip():
            raise SceneSplitterError(
                "Script cannot be empty."
            )

        # Normalize whitespace
        cleaned_script = re.sub(
            r"\s+",
            " ",
            script,
        ).strip()

        # Split primarily at sentence boundaries.
        sentences = re.split(
            r"(?<=[.!?])\s+",
            cleaned_script,
        )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        if not sentences:
            raise SceneSplitterError(
                "No sentences were found in the script."
            )

        scenes = []

        # Group approximately 2 sentences per scene.
        current_scene = []

        for sentence in sentences:

            current_scene.append(sentence)

            if len(current_scene) >= 2:
                scenes.append(
                    " ".join(current_scene)
                )
                current_scene = []

        # Add remaining sentence.
        if current_scene:
            scenes.append(
                " ".join(current_scene)
            )

        return scenes