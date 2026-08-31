import json
from pathlib import Path

from app.schemas.scene import Scene


class ScriptLoaderError(Exception):
    """Raised when the script file cannot be loaded."""


class ScriptLoader:

    def load(
        self,
        script_path: str,
    ) -> tuple[str, list[Scene], str]:

        path = Path(script_path)

        if not path.exists():
            raise ScriptLoaderError(
                f"Script file not found: {path}"
            )

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except json.JSONDecodeError as exc:
            raise ScriptLoaderError(
                f"Invalid JSON in script file: {path}"
            ) from exc

        # -----------------------------------
        # Validate title
        # -----------------------------------

        title = data.get("title")

        if not title:
            raise ScriptLoaderError(
                "Script title is required."
            )

        # -----------------------------------
        # Validate scenes
        # -----------------------------------

        scene_data = data.get("scenes")

        if not isinstance(
            scene_data,
            list,
        ):
            raise ScriptLoaderError(
                "The 'scenes' field must be a list."
            )

        if not scene_data:
            raise ScriptLoaderError(
                "At least one scene is required."
            )

        # -----------------------------------
        # Validate voice
        # -----------------------------------

        voice_id = data.get("voice_id")

        if not voice_id:
            raise ScriptLoaderError(
                "The 'voice_id' field is required."
            )

        # -----------------------------------
        # Convert JSON scenes to Scene objects
        # -----------------------------------

        scenes = []

        for index, item in enumerate(
            scene_data,
            start=1,
        ):

            if not isinstance(item, dict):
                raise ScriptLoaderError(
                    f"Scene {index} must be an object."
                )

            scene_id = item.get("scene_id")
            narration = item.get("narration")
            visual_prompt = item.get(
                "visual_prompt"
            )

            if scene_id is None:
                raise ScriptLoaderError(
                    f"Scene {index} is missing "
                    "'scene_id'."
                )

            if not narration:
                raise ScriptLoaderError(
                    f"Scene {scene_id} is missing "
                    "'narration'."
                )

            if not visual_prompt:
                raise ScriptLoaderError(
                    f"Scene {scene_id} is missing "
                    "'visual_prompt'."
                )

            scenes.append(
                Scene(
                    scene_id=scene_id,
                    narration=narration,
                    visual_prompt=visual_prompt,
                )
            )

        return title, scenes, voice_id