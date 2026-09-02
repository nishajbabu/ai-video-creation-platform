from app.core.startup import initialize_application
from app.llm.config import LLMConfig

from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.anthropic_provider import AnthropicProvider


initialize_application()

config = LLMConfig()

provider_classes = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "anthropic": AnthropicProvider,
}


for provider_name in [
    "openai",
    "gemini",
    "groq",
    "anthropic",
]:
    print()
    print("=" * 60)
    print(f"TESTING {provider_name.upper()}")
    print("=" * 60)

    keys = [
        key
        for key in config.get_keys()
        if key.provider == provider_name
    ]

    if not keys:
        print("NO KEYS CONFIGURED")
        continue

    provider_class = provider_classes[provider_name]

    for key in keys:
        print()
        print(f"Key: {key.key_id}")
        print(f"Model: {key.model}")

        try:
            provider = provider_class(
                api_key=key.api_key,
                key_id=key.key_id,
                model=key.model,
                timeout=30.0,
            )

            result = provider.generate(
                "Reply with exactly OK.",
                max_tokens=5,
            )

            print("RESULT:", result)
            print("STATUS: SUCCESS")

        except Exception as exc:
            print("STATUS: FAILED")
            print("ERROR TYPE:", type(exc).__name__)
            print("ERROR:", str(exc))