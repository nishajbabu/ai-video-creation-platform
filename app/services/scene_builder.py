from app.schemas.scene import Scene
from app.services.scene_splitter import SceneSplitter
from app.services.visual_prompt_generator import (
    VisualPromptGenerator,
)


class SceneBuilder:

    def __init__(self):
        self.scene_splitter = SceneSplitter()
        self.prompt_generator = (
            VisualPromptGenerator()
        )

    def build(
        self,
        script: str,
    ) -> list[Scene]:

        if not script or not script.strip():
            raise ValueError(
                "Script cannot be empty."
            )

        narrations = self.scene_splitter.split(
            script
        )

        scenes = []

        for scene_id, narration in enumerate(
            narrations,
            start=1,
        ):

            visual_prompt = (
                self.prompt_generator.generate(
                    narration
                )
            )

            scene = Scene(
                scene_id=scene_id,
                narration=narration,
                visual_prompt=visual_prompt,
            )

            scenes.append(scene)

        return scenes