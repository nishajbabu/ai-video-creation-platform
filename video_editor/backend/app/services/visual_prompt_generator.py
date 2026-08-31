class VisualPromptGenerator:

    def generate(
        self,
        narration: str,
    ) -> str:

        if not narration or not narration.strip():
            raise ValueError(
                "Narration cannot be empty."
            )

        narration = narration.strip()

        prompt = (
            "Create a realistic cinematic visual "
            "representing the following scene: "
            f"{narration} "
            "Show the main subjects clearly. "
            "Use realistic natural lighting, "
            "detailed surroundings, realistic textures, "
            "natural colors, cinematic composition, "
            "and a professional documentary style."
        )

        return prompt