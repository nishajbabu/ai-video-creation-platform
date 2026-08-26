import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg

from app.providers.video.provider import VideoProvider


class LocalVideoProvider(VideoProvider):

    def __init__(self):
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    def _get_audio_duration(
        self,
        audio_path: Path,
    ) -> float:

        command = [
            self.ffmpeg,
            "-i",
            str(audio_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        output = result.stderr

        for line in output.splitlines():

            if "Duration:" not in line:
                continue

            duration_text = (
                line.split("Duration:")[1]
                .split(",")[0]
                .strip()
            )

            hours, minutes, seconds = duration_text.split(":")

            return (
                int(hours) * 3600
                + int(minutes) * 60
                + float(seconds)
            )

        raise RuntimeError(
            "Could not determine audio duration."
        )

    def generate_video(
        self,
        prompt: str,
        image_url: str | None = None,
        audio_url: str | None = None,
        duration: int = 5,
    ) -> bytes:

        if not image_url:
            raise ValueError(
                "An image path is required."
            )

        image_path = Path(image_url)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image file not found: {image_path}"
            )

        # -----------------------------------
        # Check audio
        # -----------------------------------

        if audio_url:
            audio_path = Path(audio_url)

            if not audio_path.exists():
                raise FileNotFoundError(
                    f"Audio file not found: {audio_path}"
                )

            actual_duration = self._get_audio_duration(
                audio_path
            )

            if actual_duration <= 0:
                raise RuntimeError(
                    "Audio duration is invalid."
                )

        else:
            audio_path = None
            actual_duration = float(duration)

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_directory = Path(temp_dir)

            output_path = (
                temp_directory
                / "generated_video.mp4"
            )

            # -----------------------------------
            # Video configuration
            # -----------------------------------

            frames_per_second = 24

            total_frames = max(
                1,
                int(
                    actual_duration
                    * frames_per_second
                ),
            )

            video_filter = (
                "scale=1920:1080:"
                "force_original_aspect_ratio=decrease,"
                "pad=1920:1080:"
                "(ow-iw)/2:"
                "(oh-ih)/2,"
                "zoompan="
                "z='min(zoom+0.0008,1.08)':"
                "x='iw/2-(iw/zoom/2)':"
                "y='ih/2-(ih/zoom/2)':"
                f"d={total_frames}:"
                "s=1920x1080:"
                "fps=24"
            )

            # -----------------------------------
            # FFmpeg command
            # -----------------------------------

            command = [
                self.ffmpeg,
                "-y",

                # Image input
                "-loop",
                "1",
                "-i",
                str(image_path),
            ]

            # Audio input
            if audio_path:
                command.extend(
                    [
                        "-i",
                        str(audio_path),
                    ]
                )

            # -----------------------------------
            # Video settings
            # -----------------------------------

            command.extend(
                [
                    "-vf",
                    video_filter,

                    "-t",
                    str(actual_duration),

                    "-c:v",
                    "libx264",

                    "-pix_fmt",
                    "yuv420p",

                    "-preset",
                    "medium",

                    "-crf",
                    "23",
                ]
            )

            # -----------------------------------
            # Audio settings
            # -----------------------------------

            if audio_path:

                command.extend(
                    [
                        "-map",
                        "0:v:0",

                        "-map",
                        "1:a:0",

                        "-c:a",
                        "aac",

                        "-b:a",
                        "128k",

                        "-ar",
                        "44100",

                        "-ac",
                        "2",

                        "-shortest",

                        "-movflags",
                        "+faststart",
                    ]
                )

            else:

                command.extend(
                    [
                        "-map",
                        "0:v:0",
                    ]
                )

            # -----------------------------------
            # Output
            # -----------------------------------

            command.append(
                str(output_path)
            )

            # -----------------------------------
            # Run FFmpeg
            # -----------------------------------

            try:

                result = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            except subprocess.CalledProcessError as exc:

                raise RuntimeError(
                    "FFmpeg failed to generate "
                    "the local video:\n"
                    f"{exc.stderr}"
                ) from exc

            # -----------------------------------
            # Validate output
            # -----------------------------------

            if not output_path.exists():

                raise RuntimeError(
                    "FFmpeg completed but the "
                    "video file was not created."
                )

            video_bytes = (
                output_path.read_bytes()
            )

            if not video_bytes:

                raise RuntimeError(
                    "Generated video is empty."
                )

            return video_bytes