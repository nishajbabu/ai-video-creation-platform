import asyncio
import edge_tts


async def main():
    voices = await edge_tts.list_voices()

    for voice in voices:
        locale = voice["Locale"]

        if locale in ["ta-IN", "en-US"]:
            print(
                f'{voice["ShortName"]} | '
                f'{voice["Gender"]} | '
                f'{voice["Locale"]}'
            )


if __name__ == "__main__":
    asyncio.run(main())