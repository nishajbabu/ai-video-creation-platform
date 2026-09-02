from pathlib import Path
import subprocess
import uuid
from urllib.parse import urlparse

from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = Path("media") / "exports"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# ASSET HELPERS
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
# PATH HELPERS
# ============================================================

def get_local_path(
    file_url: str,
) -> Path:
    """
    Convert a media URL/path into a local filesystem Path.

    Supported examples:

        media/images/example.png
        /media/images/example.png
        \\media\\images\\example.png
        images/example.png
        videos/example.mp4
        audio/example.mp3
        http://127.0.0.1:8001/media/images/example.png
    """

    if not file_url:
        raise ValueError(
            "Media file URL/path cannot be empty."
        )

    normalized = str(file_url).strip()

    # Windows path -> slash style
    normalized = normalized.replace("\\", "/")

    # HTTP/HTTPS URL
    if "://" in normalized:
        parsed = urlparse(normalized)
        normalized = parsed.path

    normalized = normalized.replace("\\", "/")

    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    normalized = normalized.lstrip("/")

    # media/whatever
    if normalized.startswith("media/"):
        return Path(normalized)

    # /something/media/whatever
    if "media/" in normalized:
        normalized = normalized.split(
            "media/",
            1,
        )[1]
        return Path("media") / normalized

    # images/...
    if normalized.startswith("images/"):
        return Path("media") / normalized

    # videos/...
    if normalized.startswith("videos/"):
        return Path("media") / normalized

    # audio/...
    if normalized.startswith("audio/"):
        return Path("media") / normalized

    return Path(normalized)


# ============================================================
# FFMPEG EXECUTION
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
# FFMPEG DRAW TEXT ESCAPING
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
# MEDIA DURATION
# ============================================================

def get_video_duration(
    input_file: Path,
) -> float:
    """
    Get the actual duration of a media file using ffprobe.

    Works for video and audio files.
    """

    if not input_file.exists():
        raise FileNotFoundError(
            f"Media file not found: {input_file}"
        )

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
            "Failed to get media duration:\n"
            + result.stderr
        )

    value = result.stdout.strip()

    try:
        duration = float(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid media duration returned "
            f"for: {input_file}"
        ) from exc

    if duration <= 0:
        raise RuntimeError(
            f"Media duration is not positive: "
            f"{input_file}"
        )

    return duration


def get_audio_duration(
    audio_file: Path,
) -> float:
    """
    Get narration/audio duration.

    This is intentionally kept separate from
    get_video_duration for clarity, while both
    use ffprobe internally.
    """

    return get_video_duration(audio_file)


# ============================================================
# CREATE VIDEO FROM IMAGE
# ============================================================

def create_video_from_image(
    image_file: Path,
    output_file: Path,
    duration: float,
):
    """
    Convert an image into a video clip.

    The image remains visible for the entire duration.
    """

    if not image_file.exists():
        raise FileNotFoundError(
            f"Image file not found: {image_file}"
        )

    if duration <= 0:
        raise ValueError(
            "Image duration must be greater than 0."
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "ffmpeg",
        "-y",

        "-loop",
        "1",

        "-i",
        str(image_file),

        "-t",
        f"{duration:.6f}",

        "-vf",
        (
            "scale=1280:720:"
            "force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
            "format=yuv420p"
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
# ADD AUDIO WITHOUT CUTTING NARRATION
# ============================================================

def add_audio_to_video(
    video_file: Path,
    audio_file: Path,
    output_file: Path,
):
    """
    Add narration to a video.

    IMPORTANT:
    There is deliberately NO '-shortest' here.

    The scene video duration is already calculated to be
    at least as long as the narration duration.

    Therefore the narration is preserved completely.
    """

    if not video_file.exists():
        raise FileNotFoundError(
            f"Video file not found: {video_file}"
        )

    if not audio_file.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_file}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    run_ffmpeg(
        command,
        "Failed to add audio to scene:",
    )


# ============================================================
# NORMALIZE EXISTING VIDEO
# ============================================================

def normalize_video(
    input_file: Path,
    output_file: Path,
    duration: float | None = None,
):
    """
    Normalize an existing video asset.

    When duration is provided, the visual is forced to the
    requested length. A small loop is used so a short source
    video can still cover a longer scene.
    """

    if not input_file.exists():
        raise FileNotFoundError(
            f"Video file not found: {input_file}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "ffmpeg",
        "-y",
    ]

    if duration is not None and duration > 0:
        command.extend(
            [
                "-stream_loop",
                "-1",
            ]
        )

    command.extend(
        [
            "-i",
            str(input_file),

            "-vf",
            (
                "scale=1280:720:"
                "force_original_aspect_ratio=decrease,"
                "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
                "format=yuv420p"
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
        ]
    )

    if duration is not None and duration > 0:
        command.extend(
            [
                "-t",
                f"{duration:.6f}",
            ]
        )

    command.extend(
        [
            "-movflags",
            "+faststart",

            str(output_file),
        ]
    )

    run_ffmpeg(
        command,
        "Failed to normalize video:",
    )


# ============================================================
# TRIM / EXTEND VIDEO
# ============================================================

def trim_video(
    input_file: Path,
    output_file: Path,
    duration: float,
):
    """
    Make a video exactly the requested duration.

    The source is looped when necessary so a shorter source
    does not cause the visual track to end before narration.
    """

    if not input_file.exists():
        raise FileNotFoundError(
            f"Video file not found: {input_file}"
        )

    if duration <= 0:
        raise ValueError(
            "Scene duration must be greater than 0."
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "ffmpeg",
        "-y",

        "-stream_loop",
        "-1",

        "-i",
        str(input_file),

        "-t",
        f"{duration:.6f}",

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
        "Failed to trim/extend video:",
    )


# ============================================================
# TEXT OVERLAY
# ============================================================

def apply_text_overlay(
    input_file: Path,
    output_file: Path,
    text: str,
):
    """
    Add text overlay near the bottom-center.
    """

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input video not found: {input_file}"
        )

    escaped_text = escape_drawtext(
        text
    )

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
# TRANSITION HELPERS
# ============================================================

SUPPORTED_TRANSITIONS = [
    "none",
    "fade",
    "fade_out",
    "crossfade",
    "dissolve",
    "wipe_left",
    "wipe_right",
    "wipe_up",
    "wipe_down",
    "slide_left",
    "slide_right",
    "slide_up",
    "slide_down",
    "circle_open",
    "circle_close",
]


TRANSITION_MAP = {
    "fade": "fade",
    "fade_in": "fade",
    "fade-out": "fade_out",
    "fadeout": "fade_out",
    "fade_out": "fade_out",
    "cross_fade": "crossfade",
    "cross-fade": "crossfade",
    "crossfade": "crossfade",
    "wipe-left": "wipe_left",
    "wipe-right": "wipe_right",
    "wipe-up": "wipe_up",
    "wipe-down": "wipe_down",
    "slide-left": "slide_left",
    "slide-right": "slide_right",
    "slide-up": "slide_up",
    "slide-down": "slide_down",
    "circle-open": "circle_open",
    "circle-close": "circle_close",
}


XFADER_TRANSITIONS = {
    "crossfade": "fade",
    "dissolve": "dissolve",
    "wipe_left": "wipeleft",
    "wipe_right": "wiperight",
    "wipe_up": "wipeup",
    "wipe_down": "wipedown",
    "slide_left": "slideleft",
    "slide_right": "slideright",
    "slide_up": "slideup",
    "slide_down": "slidedown",
    "circle_open": "circleopen",
    "circle_close": "circleclose",
}


def normalize_transition(
    transition: str | None,
) -> str:
    """
    Normalize transition values from the editor.

    Empty or unknown transitions are treated as no transition.
    """

    if not transition:
        return "none"

    value = str(transition).strip().lower()

    if value in {"", "none", "no_transition", "no-transition"}:
        return "none"

    value = TRANSITION_MAP.get(
        value,
        value,
    )

    if value not in SUPPORTED_TRANSITIONS:
        return "none"

    return value


# ============================================================
# FADE-IN TRANSITION
# ============================================================

def apply_fade_transition(
    input_file: Path,
    output_file: Path,
    duration: float = 0.5,
):
    """
    Apply a fade-in at the beginning of a scene.
    """

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input video not found: {input_file}"
        )

    fade_duration = min(
        0.5,
        max(0.1, float(duration)),
    )

    filter_text = (
        f"fade=t=in:st=0:d={fade_duration:.6f}"
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
# FADE-OUT TRANSITION
# ============================================================

def apply_fade_out(
    input_file: Path,
    output_file: Path,
    duration: float,
):
    """
    Apply a fade-out at the end of a scene.
    """

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input video not found: {input_file}"
        )

    if duration <= 0:
        raise ValueError(
            "Fade-out duration must be positive."
        )

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
        f"st={start_time:.6f}:"
        f"d={fade_duration:.6f}"
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
# CHECK AUDIO STREAM
# ============================================================

def has_audio_stream(
    input_file: Path,
) -> bool:
    """
    Return True when the media file contains an audio stream.
    """

    if not input_file.exists():
        return False

    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        str(input_file),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    return bool(
        result.returncode == 0
        and result.stdout.strip()
    )


# ============================================================
# CROSSFADE / TRANSITION BETWEEN TWO SCENES
# ============================================================

def apply_scene_transition(
    first_file: Path,
    second_file: Path,
    output_file: Path,
    transition: str,
    first_duration: float,
    second_duration: float,
    transition_duration: float = 0.5,
):
    """
    Join two rendered scene clips using an FFmpeg xfade transition.

    The transition belongs to the second scene in the editor:
    its selected transition describes how the previous scene
    changes into this scene.
    """

    if not first_file.exists():
        raise FileNotFoundError(
            f"First transition video not found: {first_file}"
        )

    if not second_file.exists():
        raise FileNotFoundError(
            f"Second transition video not found: {second_file}"
        )

    transition = normalize_transition(
        transition
    )

    if transition not in XFADER_TRANSITIONS:
        raise ValueError(
            f"Transition '{transition}' does not support "
            "two-scene xfade processing."
        )

    overlap = min(
        0.75,
        max(0.1, transition_duration),
        max(0.1, first_duration / 2),
        max(0.1, second_duration / 2),
    )

    first_has_audio = has_audio_stream(
        first_file
    )
    second_has_audio = has_audio_stream(
        second_file
    )

    xfade_name = XFADER_TRANSITIONS[
        transition
    ]

    offset = max(
        0.0,
        float(first_duration) - overlap,
    )

    if first_has_audio and second_has_audio:

        filter_complex = (
            f"[0:v][1:v]xfade="
            f"transition={xfade_name}:"
            f"duration={overlap:.6f}:"
            f"offset={offset:.6f}[v];"
            f"[0:a][1:a]acrossfade="
            f"d={overlap:.6f}[a]"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(first_file),
            "-i",
            str(second_file),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
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

    else:
        # When a scene has no audio stream, use video xfade and
        # generate silent audio so the final editor output remains
        # compatible with the normal MP4 export path.
        filter_complex = (
            f"[0:v][1:v]xfade="
            f"transition={xfade_name}:"
            f"duration={overlap:.6f}:"
            f"offset={offset:.6f}[v]"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(first_file),
            "-i",
            str(second_file),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_file),
        ]

    run_ffmpeg(
        command,
        f"Failed to apply {transition} transition:",
    )


# ============================================================
# TIMELINE HELPERS
# ============================================================
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
    Determine the requested scene duration.

    Priority:

        1. Timeline duration
        2. Scene duration
    """

    if timeline:

        timeline_duration = (
            float(timeline.end_time)
            - float(timeline.start_time)
        )

        if timeline_duration > 0:
            return timeline_duration

    if scene.duration and scene.duration > 0:
        return float(scene.duration)

    raise ValueError(
        f"Invalid duration for scene {scene.id}"
    )


# ============================================================
# IMPORTANT:
# GET SAFE SCENE DURATION
# ============================================================

def get_safe_scene_duration(
    scene: Scene,
    assets: list[Asset],
    timeline: Timeline | None,
) -> float:
    """
    Calculate the actual render duration.

    RULE:

        final duration =
            max(
                editor/timeline duration,
                narration duration
            )

    This guarantees that reducing the scene duration
    cannot cut the narration.
    """

    requested_duration = get_scene_duration(
        scene,
        timeline,
    )

    audio_url = get_scene_audio(
        scene.id,
        assets,
    )

    if not audio_url:
        return requested_duration

    audio_file = get_local_path(
        audio_url
    )

    if not audio_file.exists():
        raise FileNotFoundError(
            f"Audio file not found for "
            f"scene {scene.id}: {audio_file}"
        )

    audio_duration = get_audio_duration(
        audio_file
    )

    return max(
        requested_duration,
        audio_duration,
    )


# ============================================================
# CREATE SCENE CLIP
# ============================================================

def create_scene_clip(
    scene: Scene,
    assets: list[Asset],
    timeline: Timeline | None,
    output_file: Path,
):
    """
    Create one complete rendered scene.

    Workflow:

        Editor duration
              +
        Narration duration protection
              ↓
        Image/video
              ↓
        Audio
              ↓
        Text overlay
              ↓
        Transition
              ↓
        Scene clip

    IMPORTANT:

    Narration is never shortened below its actual duration.
    """

    # ========================================================
    # 1. DETERMINE SAFE DURATION
    # ========================================================

    duration = get_safe_scene_duration(
        scene=scene,
        assets=assets,
        timeline=timeline,
    )

    # ========================================================
    # 2. GET ASSETS
    # ========================================================

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

    if not image_url and not video_url:
        raise ValueError(
            f"Scene {scene.id} has no image "
            f"or video asset."
        )

    # ========================================================
    # 3. TEMP DIRECTORY
    # ========================================================

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
        # 4. CREATE VISUAL
        # ====================================================

        if image_url:

            image_file = get_local_path(
                image_url
            )

            if not image_file.exists():
                raise FileNotFoundError(
                    f"Image file not found for "
                    f"scene {scene.id}: "
                    f"{image_file}"
                )

            visual_file = (
                scene_dir / "visual.mp4"
            )

            create_video_from_image(
                image_file=image_file,
                output_file=visual_file,
                duration=duration,
            )

        else:

            video_file = get_local_path(
                video_url
            )

            if not video_file.exists():
                raise FileNotFoundError(
                    f"Video file not found for "
                    f"scene {scene.id}: "
                    f"{video_file}"
                )

            visual_file = (
                scene_dir / "visual.mp4"
            )

            normalize_video(
                input_file=video_file,
                output_file=visual_file,
                duration=duration,
            )

        current_file = visual_file

        # ====================================================
        # 5. ADD NARRATION
        # ====================================================

        if audio_url:

            audio_file = get_local_path(
                audio_url
            )

            if not audio_file.exists():
                raise FileNotFoundError(
                    f"Audio file not found for "
                    f"scene {scene.id}: "
                    f"{audio_file}"
                )

            audio_duration = get_audio_duration(
                audio_file
            )

            # The visual should always cover the narration.
            if audio_duration > duration:
                duration = audio_duration

            audio_video_file = (
                scene_dir / "audio.mp4"
            )

            add_audio_to_video(
                video_file=current_file,
                audio_file=audio_file,
                output_file=audio_video_file,
            )

            current_file = audio_video_file

        # ====================================================
        # 6. TEXT OVERLAY
        # ====================================================

        if (
            timeline
            and timeline.text_overlay
            and timeline.text_overlay.strip()
        ):

            text_file = (
                scene_dir / "text.mp4"
            )

            apply_text_overlay(
                input_file=current_file,
                output_file=text_file,
                text=timeline.text_overlay,
            )

            current_file = text_file

        # ====================================================
        # 7. SCENE-LEVEL TRANSITION EFFECT
        # ====================================================

        transition = normalize_transition(
            timeline.transition
            if timeline
            else None
        )

        # Crossfade/wipe/slide/circle transitions require two
        # adjacent scene inputs, so they are applied later in
        # render_video(). Fade and fade-out can be safely applied
        # to this individual scene here.

        if transition == "fade":

            fade_file = (
                scene_dir / "fade.mp4"
            )

            apply_fade_transition(
                input_file=current_file,
                output_file=fade_file,
                duration=min(0.5, duration),
            )

            current_file = fade_file

        elif transition == "fade_out":

            fade_out_file = (
                scene_dir / "fade_out.mp4"
            )

            apply_fade_out(
                input_file=current_file,
                output_file=fade_out_file,
                duration=duration,
            )

            current_file = fade_out_file

        # ====================================================
        # 8. FINALIZE SCENE
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

        # ====================================================
        # 9. VERIFY
        # ====================================================

        if not output_file.exists():
            raise RuntimeError(
                f"Final scene file was not created "
                f"for scene {scene.id}."
            )

        if output_file.stat().st_size == 0:
            raise RuntimeError(
                f"Final scene file is empty "
                f"for scene {scene.id}."
            )

    finally:

        # ====================================================
        # CLEANUP
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
# CONCATENATE FINAL VIDEO
# ============================================================

def render_video(
    video_id: int,
    scenes: list[Scene],
    assets: list[Asset],
    timeline_items: list[Timeline],
):
    """
    Render the complete editor project into one MP4.
    """

    ordered_scenes = sorted(
        scenes,
        key=lambda scene: scene.order,
    )

    if not ordered_scenes:
        raise ValueError(
            "No scenes available for export."
        )

    temp_dir = (
        OUTPUT_DIR
        / f"temp_{uuid.uuid4().hex}"
    )

    temp_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    processed_files: list[Path] = []

    try:

        # ====================================================
        # PROCESS EACH SCENE
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

        if not processed_files:
            raise ValueError(
                "No scene videos were generated."
            )

        # ====================================================
        # CREATE CONCAT LIST
        # ====================================================

        concat_file = (
            temp_dir / "concat.txt"
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
                    .replace("'", "'\\''")
                )

                file.write(
                    f"file '{path_string}'\n"
                )

        # ====================================================
        # FINAL OUTPUT
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
        # BUILD FINAL VIDEO WITH SELECTED TRANSITIONS
        # ====================================================

        current_file = processed_files[0]

        for index in range(1, len(processed_files)):

            current_scene = ordered_scenes[index]

            current_timeline = get_scene_timeline(
                current_scene.id,
                timeline_items,
            )

            transition = normalize_transition(
                current_timeline.transition
                if current_timeline
                else None
            )

            next_file = processed_files[index]

            # ------------------------------------------------
            # Two-scene transitions
            # ------------------------------------------------

            if transition in XFADER_TRANSITIONS:

                first_duration = get_video_duration(
                    current_file
                )

                second_duration = get_video_duration(
                    next_file
                )

                transition_file = (
                    temp_dir
                    / f"transition_{index}.mp4"
                )

                apply_scene_transition(
                    first_file=current_file,
                    second_file=next_file,
                    output_file=transition_file,
                    transition=transition,
                    first_duration=first_duration,
                    second_duration=second_duration,
                )

                current_file = transition_file

            else:

                # ------------------------------------------------
                # Normal sequential append.
                # ------------------------------------------------

                append_file = (
                    temp_dir
                    / f"append_{index}.mp4"
                )

                append_list = (
                    temp_dir
                    / f"append_{index}.txt"
                )

                with append_list.open(
                    "w",
                    encoding="utf-8",
                ) as file:

                    for source_file in [
                        current_file,
                        next_file,
                    ]:

                        absolute_path = (
                            source_file.resolve()
                        )

                        path_string = (
                            absolute_path
                            .as_posix()
                            .replace("'", "'\\''")
                        )

                        file.write(
                            f"file '{path_string}'\n"
                        )

                command = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(append_list),
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
                    str(append_file),
                ]

                run_ffmpeg(
                    command,
                    "FFmpeg sequential append failed:",
                )

                current_file = append_file

        # ------------------------------------------------
        # Copy/re-encode the assembled result to the final path.
        # ------------------------------------------------

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(current_file),
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
        # VERIFY FINAL OUTPUT
        # ====================================================

        if not output_path.exists():
            raise RuntimeError(
                "Final output video was not created."
            )

        if output_path.stat().st_size == 0:
            raise RuntimeError(
                "Final output video is empty."
            )

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
        # CLEANUP
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