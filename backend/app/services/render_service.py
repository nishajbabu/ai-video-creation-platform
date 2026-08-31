from pathlib import Path
import subprocess
import uuid
from urllib.parse import urlparse

from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline


# ============================================================
# Output directory
# ============================================================

OUTPUT_DIR = Path("media") / "exports"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Asset helpers
# ============================================================

def get_scene_asset(
    scene_id: int,
    assets: list[Asset],
    asset_type: str,
):
    """
    Find an asset of a specific type belonging to a scene.
    """

    for asset in assets:
        if (
            asset.scene_id == scene_id
            and asset.asset_type == asset_type
        ):
            return asset.file_url

    return None


def get_scene_image(
    scene_id: int,
    assets: list[Asset],
):
    return get_scene_asset(
        scene_id,
        assets,
        "image",
    )


def get_scene_audio(
    scene_id: int,
    assets: list[Asset],
):
    return get_scene_asset(
        scene_id,
        assets,
        "audio",
    )


def get_scene_video(
    scene_id: int,
    assets: list[Asset],
):
    return get_scene_asset(
        scene_id,
        assets,
        "video",
    )


# ============================================================
# Convert media URL/path to local filesystem path
# ============================================================

def get_local_path(
    file_url: str,
) -> Path:
    """
    Convert different media path formats into a local
    filesystem path.

    Supported examples:

        media/images/example.png

        /media/images/example.png

        \\media\\images\\example.png

        images/example.png

        \\images\\example.png

        http://127.0.0.1:8001/media/images/example.png
    """

    if not file_url:
        raise ValueError(
            "Media file URL/path cannot be empty."
        )

    normalized = str(file_url).strip()

    # --------------------------------------------------------
    # Convert Windows separators to URL-style separators
    # --------------------------------------------------------

    normalized = normalized.replace("\\", "/")

    # --------------------------------------------------------
    # Handle complete HTTP/HTTPS URL
    # --------------------------------------------------------

    if "://" in normalized:

        parsed = urlparse(normalized)

        normalized = parsed.path

    # --------------------------------------------------------
    # Normalize again
    # --------------------------------------------------------

    normalized = normalized.replace("\\", "/")

    # Remove duplicate slashes
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    # --------------------------------------------------------
    # Remove leading slash
    # --------------------------------------------------------

    normalized = normalized.lstrip("/")

    # --------------------------------------------------------
    # If path contains /media/, keep everything after it
    # --------------------------------------------------------

    if "media/" in normalized:

        normalized = normalized.split(
            "media/",
            1,
        )[1]

        normalized = f"media/{normalized}"

    # --------------------------------------------------------
    # Already starts with media/
    # --------------------------------------------------------

    elif normalized.startswith("media/"):

        pass

    # --------------------------------------------------------
    # If only images/videos/audio path was stored
    # --------------------------------------------------------

    elif normalized.startswith("images/"):

        normalized = f"media/{normalized}"

    elif normalized.startswith("videos/"):

        normalized = f"media/{normalized}"

    elif normalized.startswith("audio/"):

        normalized = f"media/{normalized}"

    # --------------------------------------------------------
    # Convert Windows drive path safely
    # --------------------------------------------------------

    return Path(normalized)


# ============================================================
# Run FFmpeg
# ============================================================

def run_ffmpeg(
    command: list[str],
    error_message: str,
):
    """
    Execute FFmpeg and raise a useful error if it fails.
    """

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"{error_message}\n"
            f"{result.stderr}"
        )

    return result


# ============================================================
# Escape drawtext text
# ============================================================

def escape_drawtext(
    text: str,
) -> str:
    """
    Escape characters that have special meaning
    inside FFmpeg drawtext.
    """

    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace(",", "\\,")
    )


# ============================================================
# Create video from image
# ============================================================

def create_video_from_image(
    image_file: Path,
    output_file: Path,
    duration: float,
):
    """
    Convert an image into a video clip.

    The image remains visible for the complete
    scene duration.
    """

    if duration <= 0:

        raise ValueError(
            "Image duration must be greater than 0."
        )

    command = [
        "ffmpeg",
        "-y",

        "-loop",
        "1",

        "-i",
        str(image_file),

        "-t",
        str(duration),

        "-vf",
        (
            "scale=1280:720:"
            "force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2"
        ),

        "-r",
        "30",

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-an",

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    run_ffmpeg(
        command,
        "Failed to create video from image:",
    )


# ============================================================
# Add audio to video
# ============================================================

def add_audio_to_video(
    video_file: Path,
    audio_file: Path,
    output_file: Path,
):
    """
    Attach narration audio to the scene video.
    """

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(video_file),

        "-i",
        str(audio_file),

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-shortest",

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    run_ffmpeg(
        command,
        "Failed to add audio to scene:",
    )


# ============================================================
# Normalize existing video
# ============================================================

def normalize_video(
    input_file: Path,
    output_file: Path,
):
    """
    Normalize an existing video asset.
    """

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(input_file),

        "-vf",
        (
            "scale=1280:720:"
            "force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2"
        ),

        "-r",
        "30",

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    run_ffmpeg(
        command,
        "Failed to normalize video:",
    )


# ============================================================
# Trim video
# ============================================================

def trim_video(
    input_file: Path,
    output_file: Path,
    duration: float,
):
    """
    Trim an existing video to the required duration.
    """

    if duration <= 0:

        raise ValueError(
            "Scene duration must be greater than 0."
        )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(input_file),

        "-t",
        str(duration),

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    run_ffmpeg(
        command,
        "Failed to trim video:",
    )


# ============================================================
# Apply text overlay
# ============================================================

def apply_text_overlay(
    input_file: Path,
    output_file: Path,
    text: str,
):
    """
    Add text overlay at the bottom-center.
    """

    escaped_text = escape_drawtext(text)

    filter_text = (
        "drawtext="
        f"text='{escaped_text}':"
        "fontcolor=white:"
        "fontsize=48:"
        "x=(w-text_w)/2:"
        "y=h-text_h-60:"
        "box=1:"
        "boxcolor=black@0.55:"
        "boxborderw=15"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(input_file),

        "-vf",
        filter_text,

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    run_ffmpeg(
        command,
        "Failed to apply text overlay:",
    )


# ============================================================
# Apply fade-in
# ============================================================

def apply_fade_transition(
    input_file: Path,
    output_file: Path,
):
    """
    Apply fade-in to the beginning of a scene.
    """

    filter_text = (
        "fade="
        "t=in:"
        "st=0:"
        "d=0.5"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(input_file),

        "-vf",
        filter_text,

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    run_ffmpeg(
        command,
        "Failed to apply fade transition:",
    )


# ============================================================
# Apply fade-out
# ============================================================

def apply_fade_out(
    input_file: Path,
    output_file: Path,
    duration: float,
):
    """
    Apply fade-out at the end of a scene.
    """

    fade_duration = min(
        0.5,
        max(0.1, duration / 2),
    )

    start_time = max(
        0,
        duration - fade_duration,
    )

    filter_text = (
        f"fade=t=out:"
        f"st={start_time}:"
        f"d={fade_duration}"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(input_file),

        "-vf",
        filter_text,

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    run_ffmpeg(
        command,
        "Failed to apply fade-out:",
    )


# ============================================================
# Timeline helpers
# ============================================================

def get_scene_timeline(
    scene_id: int,
    timeline_items: list[Timeline],
):
    """
    Find timeline information for a scene.
    """

    for item in timeline_items:

        if item.scene_id == scene_id:
            return item

    return None


def get_scene_duration(
    scene: Scene,
    timeline: Timeline | None,
):
    """
    Determine scene duration.

    Priority:

        1. Timeline duration
        2. Scene duration
    """

    if timeline:

        timeline_duration = (
            timeline.end_time
            - timeline.start_time
        )

        if timeline_duration > 0:

            return float(
                timeline_duration
            )

    if scene.duration and scene.duration > 0:

        return float(
            scene.duration
        )

    raise ValueError(
        f"Invalid duration for scene {scene.id}"
    )


# ============================================================
# Create scene clip
# ============================================================

def create_scene_clip(
    scene: Scene,
    assets: list[Asset],
    timeline: Timeline | None,
    output_file: Path,
):
    """
    Create one complete scene clip.

    REQUIRED WORKFLOW:

        AI image
            ↓
        image → video
            ↓
        narration audio
            ↓
        text overlay
            ↓
        transition
            ↓
        scene clip

    Existing video assets are supported as a fallback,
    but IMAGE is preferred whenever an image exists.
    """

    duration = get_scene_duration(
        scene,
        timeline,
    )

    image_url = get_scene_image(
        scene.id,
        assets,
    )

    audio_url = get_scene_audio(
        scene.id,
        assets,
    )

    video_url = get_scene_video(
        scene.id,
        assets,
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Prefer IMAGE over VIDEO.
    #
    # This prevents the renderer from trying to use:
    #
    # videos/ai_final_test_001_scene_1.mp4
    #
    # when the workflow is supposed to use:
    #
    # images/ai_final_test_001_scene_1.png
    # --------------------------------------------------------

    if not image_url and not video_url:

        raise ValueError(
            f"Scene {scene.id} has no image or video asset."
        )

    # --------------------------------------------------------
    # Temporary directory
    # --------------------------------------------------------

    scene_dir = (
        output_file.parent
        / f"scene_{scene.id}_{uuid.uuid4().hex}"
    )

    scene_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        # ====================================================
        # 1. Create visual clip
        # ====================================================

        if image_url:

            image_file = get_local_path(
                image_url
            )

            if not image_file.exists():

                raise ValueError(
                    f"Image file not found for "
                    f"scene {scene.id}: "
                    f"{image_file}"
                )

            visual_file = (
                scene_dir
                / "visual.mp4"
            )

            create_video_from_image(
                image_file=image_file,
                output_file=visual_file,
                duration=duration,
            )

        else:

            # ------------------------------------------------
            # Fallback:
            # use existing video only if no image exists
            # ------------------------------------------------

            video_file = get_local_path(
                video_url
            )

            if not video_file.exists():

                raise ValueError(
                    f"Video file not found for "
                    f"scene {scene.id}: "
                    f"{video_file}"
                )

            visual_file = (
                scene_dir
                / "visual.mp4"
            )

            normalize_video(
                input_file=video_file,
                output_file=visual_file,
            )

            trimmed_file = (
                scene_dir
                / "trimmed.mp4"
            )

            trim_video(
                input_file=visual_file,
                output_file=trimmed_file,
                duration=duration,
            )

            visual_file = trimmed_file

        current_file = visual_file

        # ====================================================
        # 2. Add narration
        # ====================================================

        if audio_url:

            audio_file = get_local_path(
                audio_url
            )

            if not audio_file.exists():

                raise ValueError(
                    f"Audio file not found for "
                    f"scene {scene.id}: "
                    f"{audio_file}"
                )

            audio_video_file = (
                scene_dir
                / "audio.mp4"
            )

            add_audio_to_video(
                video_file=current_file,
                audio_file=audio_file,
                output_file=audio_video_file,
            )

            current_file = audio_video_file

        # ====================================================
        # 3. Add text overlay
        # ====================================================

        if (
            timeline
            and timeline.text_overlay
            and timeline.text_overlay.strip()
        ):

            text_file = (
                scene_dir
                / "text.mp4"
            )

            apply_text_overlay(
                input_file=current_file,
                output_file=text_file,
                text=timeline.text_overlay,
            )

            current_file = text_file

        # ====================================================
        # 4. Apply transition
        # ====================================================

        if (
            timeline
            and timeline.transition
        ):

            transition = (
                timeline.transition
                .strip()
                .lower()
            )

            if transition == "fade":

                fade_file = (
                    scene_dir
                    / "fade.mp4"
                )

                apply_fade_transition(
                    input_file=current_file,
                    output_file=fade_file,
                )

                current_file = fade_file

        # ====================================================
        # 5. Copy final scene clip
        # ====================================================

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        command = [
            "ffmpeg",
            "-y",

            "-i",
            str(current_file),

            "-c",
            "copy",

            str(output_file),
        ]

        run_ffmpeg(
            command,
            f"Failed to finalize scene {scene.id}:",
        )

    finally:

        # ====================================================
        # Cleanup temporary scene directory
        # ====================================================

        if scene_dir.exists():

            for file in scene_dir.iterdir():

                try:
                    file.unlink()

                except Exception:
                    pass

            try:
                scene_dir.rmdir()

            except Exception:
                pass


# ============================================================
# Render final video
# ============================================================

def render_video(
    video_id: int,
    scenes: list[Scene],
    assets: list[Asset],
    timeline_items: list[Timeline],
):
    """
    Render the complete editor project into ONE MP4.

    Workflow:

        Scene 1 image
             +
        Scene 1 audio
             +
        Scene 1 text
             +
        Scene 1 transition

                ↓

        Scene 2 image
             +
        Scene 2 audio
             +
        Scene 2 text
             +
        Scene 2 transition

                ↓

        Scene 3 image
             +
        Scene 3 audio
             +
        Scene 3 text
             +
        Scene 3 transition

                ↓

             FFmpeg

                ↓

        ONE final MP4
    """

    ordered_scenes = sorted(
        scenes,
        key=lambda scene: scene.order,
    )

    if not ordered_scenes:

        raise ValueError(
            "No scenes available for export."
        )

    # ========================================================
    # Temporary directory
    # ========================================================

    temp_dir = (
        OUTPUT_DIR
        / f"temp_{uuid.uuid4().hex}"
    )

    temp_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    processed_files = []

    try:

        # ====================================================
        # Process every scene
        # ====================================================

        for index, scene in enumerate(
            ordered_scenes,
            start=1,
        ):

            timeline = get_scene_timeline(
                scene.id,
                timeline_items,
            )

            scene_file = (
                temp_dir
                / f"scene_{index}.mp4"
            )

            create_scene_clip(
                scene=scene,
                assets=assets,
                timeline=timeline,
                output_file=scene_file,
            )

            if not scene_file.exists():

                raise RuntimeError(
                    f"Scene video was not created "
                    f"for scene {scene.id}."
                )

            processed_files.append(
                scene_file
            )

        # ====================================================
        # Validate scene clips
        # ====================================================

        if not processed_files:

            raise ValueError(
                "No scene videos were generated."
            )

        # ====================================================
        # Create concat file
        # ====================================================

        concat_file = (
            temp_dir
            / "concat.txt"
        )

        with concat_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            for processed_file in processed_files:

                absolute_path = (
                    processed_file.resolve()
                )

                path_string = (
                    absolute_path
                    .as_posix()
                    .replace(
                        "'",
                        "'\\''",
                    )
                )

                file.write(
                    f"file '{path_string}'\n"
                )

        # ====================================================
        # Final output
        # ====================================================

        output_filename = (
            f"video_{video_id}_"
            f"{uuid.uuid4().hex}.mp4"
        )

        output_path = (
            OUTPUT_DIR
            / output_filename
        )

        # ====================================================
        # Concatenate all scenes
        # ====================================================

        command = [
            "ffmpeg",
            "-y",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            str(concat_file),

            "-c:v",
            "libx264",

            "-preset",
            "medium",

            "-crf",
            "23",

            "-pix_fmt",
            "yuv420p",

            "-c:a",
            "aac",

            "-b:a",
            "128k",

            "-movflags",
            "+faststart",

            str(output_path),
        ]

        run_ffmpeg(
            command,
            "FFmpeg final export failed:",
        )

        # ====================================================
        # Verify final output
        # ====================================================

        if not output_path.exists():

            raise RuntimeError(
                "Final output video was not created."
            )

        if output_path.stat().st_size == 0:

            raise RuntimeError(
                "Final output video is empty."
            )

        # ====================================================
        # Return result
        # ====================================================

        return {
            "file_path": str(
                output_path
            ),

            "file_url": (
                f"/media/exports/"
                f"{output_filename}"
            ),
        }

    finally:

        # ====================================================
        # Cleanup temporary directory
        # ====================================================

        if temp_dir.exists():

            for file in temp_dir.iterdir():

                try:
                    file.unlink()

                except Exception:
                    pass

            try:
                temp_dir.rmdir()

            except Exception:
                pass


# ============================================================
# Get video duration
# ============================================================

def get_video_duration(
    input_file: Path,
) -> float:
    """
    Get actual media duration using FFprobe.
    """

    command = [
        "ffprobe",

        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(input_file),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            "Failed to get video duration:\n"
            + result.stderr
        )

    try:

        return float(
            result.stdout.strip()
        )

    except ValueError as exc:

        raise RuntimeError(
            f"Invalid video duration returned "
            f"for: {input_file}"
        ) from exc