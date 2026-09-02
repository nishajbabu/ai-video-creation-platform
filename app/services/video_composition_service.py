import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg


class VideoCompositionError(Exception):
    """Raised when video composition fails."""


class VideoCompositionService:

    def __init__(self):
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    def concatenate_videos(
        self,
        video_paths: list[str],
        output_path: str,
    ) -> str:

        if not video_paths:
            raise ValueError(
                "At least one video is required."
            )

        paths = [
            Path(video_path)
            for video_path in video_paths
        ]

        for path in paths:
            if not path.exists():
                raise FileNotFoundError(
                    f"Video file not found: {path}"
                )

        output = Path(output_path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:

                concat_file = (
                    Path(temp_dir) / "videos.txt"
                )

                with concat_file.open(
                    "w",
                    encoding="utf-8",
                ) as file:

                    for path in paths:
                        absolute_path = path.resolve()

                        escaped_path = str(
                            absolute_path
                        ).replace(
                            "'",
                            "'\\''",
                        )

                        file.write(
                            f"file '{escaped_path}'\n"
                        )

                command = [
                    self.ffmpeg,
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c",
                    "copy",
                    str(output),
                ]

                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                )

        except subprocess.CalledProcessError as exc:
            raise VideoCompositionError(
                "FFmpeg failed while "
                "concatenating videos:\n"
                f"{exc.stderr}"
            ) from exc

        if not output.exists():
            raise VideoCompositionError(
                "Video composition completed but "
                "the output file was not created."
            )

        if output.stat().st_size == 0:
            raise VideoCompositionError(
                "The composed video is empty."
            )

        return str(output)