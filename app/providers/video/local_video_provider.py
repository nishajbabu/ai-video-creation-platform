import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg

from app.providers.video.provider import VideoProvider


class LocalVideoProvider(VideoProvider):

    def __init__(self):
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    # ============================================================
    # GET AUDIO DURATION
    # ============================================================

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

    # ============================================================
    # GENERATE ONE SCENE VIDEO
    # ============================================================

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

        # --------------------------------------------------------
        # Check audio
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Temporary directory
        # --------------------------------------------------------

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_directory = Path(temp_dir)

            output_path = (
                temp_directory
                / "generated_video.mp4"
            )

            # ----------------------------------------------------
            # Video configuration
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # FFmpeg command
            # ----------------------------------------------------

            command = [
                self.ffmpeg,
                "-y",

                # Image input
                "-loop",
                "1",
                "-i",
                str(image_path),
            ]

            # ----------------------------------------------------
            # Audio input
            # ----------------------------------------------------

            if audio_path:

                command.extend(
                    [
                        "-i",
                        str(audio_path),
                    ]
                )

            # ----------------------------------------------------
            # Video settings
            # ----------------------------------------------------

            command.extend(
                [
                    "-vf",
                    video_filter,

                    "-t",
                    str(actual_duration),

                    "-r",
                    "24",

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

            # ----------------------------------------------------
            # Audio settings
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # Output
            # ----------------------------------------------------

            command.append(
                str(output_path)
            )

            # ----------------------------------------------------
            # Run FFmpeg
            # ----------------------------------------------------

            try:

                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            except subprocess.CalledProcessError as exc:

                raise RuntimeError(
                    "FFmpeg failed to generate "
                    "the local scene video:\n"
                    f"{exc.stderr}"
                ) from exc

            # ----------------------------------------------------
            # Validate output
            # ----------------------------------------------------

            if not output_path.exists():

                raise RuntimeError(
                    "FFmpeg completed but the "
                    "scene video was not created."
                )

            video_bytes = (
                output_path.read_bytes()
            )

            if not video_bytes:

                raise RuntimeError(
                    "Generated scene video is empty."
                )

            return video_bytes

    # ============================================================
    # COMBINE MULTIPLE SCENE VIDEOS
    # ============================================================

    def combine_videos(
        self,
        video_paths: list[str],
    ) -> bytes:

        # --------------------------------------------------------
        # Validate input
        # --------------------------------------------------------

        if not video_paths:

            raise ValueError(
                "At least one video is required "
                "to create the final video."
            )

        paths: list[Path] = []

        for video_path in video_paths:

            path = Path(video_path)

            if not path.exists():

                raise FileNotFoundError(
                    f"Scene video file not found: {path}"
                )

            if path.stat().st_size == 0:

                raise RuntimeError(
                    f"Scene video is empty: {path}"
                )

            paths.append(path)

        # --------------------------------------------------------
        # One scene
        # --------------------------------------------------------

        if len(paths) == 1:

            return paths[0].read_bytes()

        # --------------------------------------------------------
        # Temporary working directory
        # --------------------------------------------------------

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_directory = Path(temp_dir)

            concat_file = (
                temp_directory
                / "concat.txt"
            )

            final_video_path = (
                temp_directory
                / "final_video.mp4"
            )

            # ----------------------------------------------------
            # Create concat file
            # ----------------------------------------------------

            try:

                with concat_file.open(
                    "w",
                    encoding="utf-8",
                ) as file:

                    for path in paths:

                        # FFmpeg concat files work best
                        # with absolute forward-slash paths.

                        safe_path = (
                            str(path.resolve())
                            .replace("\\", "/")
                        )

                        # Escape single quotes for FFmpeg.
                        safe_path = safe_path.replace(
                            "'",
                            "'\\''"
                        )

                        file.write(
                            f"file '{safe_path}'\n"
                        )

            except OSError as exc:

                raise RuntimeError(
                    "Could not create the FFmpeg "
                    "concat file."
                ) from exc

            # ----------------------------------------------------
            # Combine videos
            #
            # Every scene generated by generate_video()
            # already has:
            #
            # 1920x1080
            # H.264
            # AAC
            # 24 FPS
            # 44100 Hz
            # Stereo
            #
            # We still re-encode here for maximum compatibility.
            # ----------------------------------------------------

            command = [
                self.ffmpeg,
                "-y",

                "-f",
                "concat",

                "-safe",
                "0",

                "-i",
                str(concat_file),

                # ------------------------------------------------
                # Video
                # ------------------------------------------------

                "-c:v",
                "libx264",

                "-preset",
                "medium",

                "-crf",
                "23",

                "-pix_fmt",
                "yuv420p",

                "-r",
                "24",

                # ------------------------------------------------
                # Audio
                # ------------------------------------------------

                "-c:a",
                "aac",

                "-b:a",
                "128k",

                "-ar",
                "44100",

                "-ac",
                "2",

                # ------------------------------------------------
                # MP4 optimization
                # ------------------------------------------------

                "-movflags",
                "+faststart",

                str(final_video_path),
            ]

            # ----------------------------------------------------
            # Run FFmpeg
            # ----------------------------------------------------

            try:

                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            except subprocess.CalledProcessError as exc:

                raise RuntimeError(
                    "FFmpeg failed to combine "
                    "the scene videos:\n"
                    f"{exc.stderr}"
                ) from exc

            # ----------------------------------------------------
            # Validate final video
            # ----------------------------------------------------

            if not final_video_path.exists():

                raise RuntimeError(
                    "FFmpeg completed but the "
                    "final combined video was not created."
                )

            final_video = (
                final_video_path.read_bytes()
            )

            if not final_video:

                raise RuntimeError(
                    "The final combined video is empty."
                )

            return final_video