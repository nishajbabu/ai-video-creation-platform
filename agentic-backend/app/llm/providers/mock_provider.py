"""
Deterministic local LLM provider used for development and end-to-end tests.

This provider never calls an external API and never consumes API credits.
It implements the same interface as the real provider adapters so the
Planner, Script, and Storyboard agents can run through the normal LLMService.
"""

import re
from typing import Any, Dict, Optional

from app.llm.base import BaseLLMProvider
from app.llm.exceptions import LLMInvalidRequestError


class MockLLMProvider(BaseLLMProvider):
    """Deterministic, zero-cost LLM adapter for local development."""

    provider_name = "mock"

    def __init__(
        self,
        api_key: str = "local",
        key_id: str = "mock_local",
        model: str = "mock-v1",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            key_id=key_id,
            model=model,
            **kwargs,
        )

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Return a deterministic text response without network access."""

        if not prompt or not prompt.strip():
            raise LLMInvalidRequestError(
                "Prompt must not be empty."
            )

        return "Local mock response."

    def generate_structured(
        self,
        prompt: str,
        *,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Return deterministic data matching the project's agent schemas."""

        if not prompt or not prompt.strip():
            raise LLMInvalidRequestError(
                "Prompt must not be empty."
            )

        if not response_schema:
            raise LLMInvalidRequestError(
                "response_schema must not be empty."
            )

        title = str(
            response_schema.get(
                "title",
                "",
            )
        )

        duration = self._extract_duration(
            prompt
        )

        if title == "VideoPlan":
            return {
                "objective": (
                    "Create a concise video based on "
                    "the user's request."
                ),
                "target_audience": None,
                "tone": None,
                "style": None,
                "duration": duration,
                "scene_count": 1,
                "content_requirements": [],
                "generation_notes": [
                    "Generated in local development mode."
                ],
            }

        if title == "Script":
            return {
                "scenes": [
                    {
                        "scene_id": 1,
                        "purpose": (
                            "Introduce the requested subject."
                        ),
                        "duration": duration,
                        "narration": (
                            "This scene introduces the "
                            "subject of the video."
                        ),
                    }
                ]
            }

        if title == "Storyboard":
            return {
                "scenes": [
                    {
                        "scene_id": 1,
                        "order": 1,
                        "duration": duration,
                        "purpose": (
                            "Introduce the requested subject."
                        ),
                        "narration": (
                            "This scene introduces the "
                            "subject of the video."
                        ),
                        "visual_description": (
                            "A clear visual introduction "
                            "of the requested subject."
                        ),
                        "visual_prompt": (
                            "Clean cinematic establishing "
                            "shot of the requested subject."
                        ),
                        "visual_type": "image",
                        "text_overlay": None,
                        "asset_requirements": [],
                        "knowledge_requirements": [],
                        "audio_requirements": {
                            "required": True,
                            "voice_style": (
                                "neutral professional"
                            ),
                            "background_music": False,
                        },
                        "transition": None,
                        "status": "planned",
                    }
                ]
            }

        return self._generic_response(
            response_schema
        )

    @staticmethod
    def _extract_duration(
        prompt: str,
    ) -> int:
        """Extract a requested duration from the prompt."""

        matches = re.findall(
            r"(?:duration|seconds?)\D{0,20}(\d+)",
            prompt,
            re.IGNORECASE,
        )

        if matches:
            value = int(
                matches[-1]
            )

            return max(
                10,
                min(
                    600,
                    value,
                ),
            )

        return 10

    @classmethod
    def _generic_response(
        cls,
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        properties = schema.get(
            "properties",
            {},
        )

        result: Dict[str, Any] = {}

        for name, definition in properties.items():
            result[name] = cls._value_for_schema(
                name,
                definition,
            )

        return result

    @classmethod
    def _value_for_schema(
        cls,
        name: str,
        definition: Dict[str, Any],
    ) -> Any:
        schema_type = definition.get(
            "type"
        )

        if schema_type == "string":
            return f"Local mock {name}."

        if schema_type == "integer":
            minimum = definition.get(
                "minimum",
                1,
            )
            return int(
                minimum
            )

        if schema_type == "number":
            return float(
                definition.get(
                    "minimum",
                    0,
                )
            )

        if schema_type == "boolean":
            return False

        if schema_type == "array":
            return []

        if schema_type == "object":
            return {
                key: cls._value_for_schema(
                    key,
                    value,
                )
                for key, value in definition.get(
                    "properties",
                    {},
                ).items()
            }

        return None