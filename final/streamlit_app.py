import os
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Frameforge | AI Video Studio",
    page_icon="F",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;700;800&display=swap'
    );

    :root {
        --ink: #172322;
        --muted: #71817c;
        --line: #d7e0da;
        --paper: #f4f6f1;
        --coral: #e7674b;
        --teal: #1d7168;
        --card: #fffef9;
        --soft: #eef3ee;
        --warning: #fff6dc;
    }

    .stApp {
        color: var(--ink);
        background: var(--paper);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: #e8eee7;
        border-right: 1px solid var(--line);
    }

    .block-container {
        max-width: 1320px;
        padding-top: 2.8rem;
        padding-bottom: 5rem;
    }

    h1,
    h2,
    h3,
    h4 {
        font-family: Manrope, sans-serif;
        letter-spacing: -1px;
    }

    h1 {
        font-size: clamp(2.8rem, 6vw, 5.2rem) !important;
        line-height: 0.98 !important;
    }

    h1 em {
        color: var(--teal);
        font-family: Georgia, serif;
        font-weight: 400;
    }

    p,
    label,
    .stMarkdown {
        font-family: Manrope, sans-serif;
    }

    .eyebrow {
        color: var(--coral);
        font: 500 10px 'DM Mono', monospace;
        letter-spacing: 1.4px;
        text-transform: uppercase;
    }

    .lede {
        max-width: 620px;
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.7;
    }

    .result-card {
        height: 100%;
        padding: 0.9rem;
        border: 1px solid var(--line);
        background: var(--card);
    }

    .final-video-card {
        padding: 1.5rem;
        border: 1px solid var(--line);
        background: var(--card);
        margin-bottom: 2rem;
    }

    .editor-heading {
        color: var(--teal);
        font-family: Manrope, sans-serif;
        font-weight: 700;
        font-size: 1.25rem;
        margin-bottom: 0.2rem;
    }

    .timeline-track {
        display: flex;
        gap: 10px;
        width: 100%;
        overflow-x: auto;
        padding: 12px 0 18px;
    }

    .timeline-item {
        min-width: 175px;
        padding: 14px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--soft);
    }

    .timeline-item strong {
        display: block;
        color: var(--teal);
        margin-bottom: 7px;
        font-family: Manrope, sans-serif;
    }

    .timeline-item small {
        color: var(--muted);
        font-family: 'DM Mono', monospace;
    }

    .status-pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        background: #e8eee7;
        color: var(--teal);
        font-size: 12px;
        font-family: 'DM Mono', monospace;
    }

    .editor-info {
        padding: 10px 14px;
        border: 1px solid var(--line);
        background: #f9fbf7;
        border-radius: 8px;
        margin: 8px 0 14px;
    }

    .editor-warning {
        padding: 10px 14px;
        border: 1px solid #ead8a5;
        background: var(--warning);
        border-radius: 8px;
        margin: 8px 0 14px;
    }

    .scene-number {
        color: var(--teal);
        font-family: 'DM Mono', monospace;
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    div.stButton > button[kind="primary"] {
        background: var(--coral);
        border: 0;
        color: white;
    }

    div.stButton > button[kind="primary"]:hover {
        background: var(--teal);
        color: white;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# URL / API HELPERS
# ============================================================

def make_absolute_url(
    api_url: str,
    value: str | None,
) -> str | None:
    """
    Convert backend media paths into browser-ready URLs.
    """

    if not value:
        return None

    value = str(value).strip()

    if value.startswith("http://") or value.startswith("https://"):
        return value

    value = value.replace("\\", "/")

    if value.startswith("/"):
        return f"{api_url}{value}"

    if value.startswith("media/"):
        return f"{api_url}/{value}"

    return f"{api_url}/media/{value}"


def api_error_message(
    response: requests.Response,
) -> str:
    """
    Extract FastAPI error detail.
    """

    try:
        data = response.json()

        if isinstance(data, dict):

            detail = data.get("detail")

            if isinstance(detail, str):
                return detail

            if detail is not None:
                return str(detail)

        return response.text

    except ValueError:
        return response.text


# ============================================================
# LOCAL MEDIA PATH HELPERS
# ============================================================

def media_url_to_local_path(
    value: str | None,
) -> Path | None:
    """
    Convert a backend media URL/path to a local Path.

    The Streamlit app and FastAPI backend are expected to run
    from the same project directory.

    Examples:
        /media/audio/test.mp3
        media/audio/test.mp3
        http://127.0.0.1:8001/media/audio/test.mp3
    """

    if not value:
        return None

    normalized = str(value).strip()

    if "://" in normalized:

        parsed = urlparse(normalized)

        normalized = parsed.path

    normalized = normalized.replace("\\", "/")
    normalized = normalized.lstrip("/")

    if normalized.startswith("media/"):

        return Path(normalized)

    if "media/" in normalized:

        relative = normalized.split(
            "media/",
            1,
        )[1]

        return Path("media") / relative

    if (
        normalized.startswith("audio/")
        or normalized.startswith("images/")
        or normalized.startswith("videos/")
        or normalized.startswith("exports/")
    ):

        return Path("media") / normalized

    return Path(normalized)


# ============================================================
# AUDIO DURATION
# ============================================================

def get_audio_duration(
    api_url: str,
    audio_value: str | None,
) -> float | None:
    """
    Get the narration duration using ffprobe.

    Returns None when the audio file is unavailable or
    ffprobe cannot read it.
    """

    if not audio_value:
        return None

    local_path = media_url_to_local_path(
        audio_value
    )

    if local_path is None:
        return None

    if not local_path.exists():
        return None

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(local_path),
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return None

        value = result.stdout.strip()

        duration = float(value)

        if duration <= 0:
            return None

        return duration

    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
    ):

        return None


# ============================================================
# API REQUEST FUNCTIONS
# ============================================================

def get_editor_data(
    api_url: str,
    video_id: int,
) -> dict[str, Any]:

    response = requests.get(
        f"{api_url}/editor/{video_id}",
        timeout=60,
    )

    if not response.ok:

        raise RuntimeError(
            f"Editor request failed "
            f"({response.status_code}): "
            f"{api_error_message(response)}"
        )

    return response.json()


def update_editor_scene(
    api_url: str,
    video_id: int,
    scene_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:

    response = requests.put(
        f"{api_url}/editor/{video_id}/scenes/{scene_id}",
        json=payload,
        timeout=60,
    )

    if not response.ok:

        raise RuntimeError(
            f"Scene update failed "
            f"({response.status_code}): "
            f"{api_error_message(response)}"
        )

    return response.json()


def reorder_editor_scenes(
    api_url: str,
    video_id: int,
    scene_ids: list[int],
) -> dict[str, Any]:

    response = requests.put(
        f"{api_url}/editor/{video_id}/reorder",
        json=scene_ids,
        timeout=60,
    )

    if not response.ok:

        raise RuntimeError(
            f"Reorder failed "
            f"({response.status_code}): "
            f"{api_error_message(response)}"
        )

    return response.json()


def delete_editor_scene(
    api_url: str,
    scene_id: int,
) -> dict[str, Any]:
    """
    Delete an editor scene using the backend scene endpoint.

    The backend route is:
        DELETE /scenes/{scene_id}
    """

    response = requests.delete(
        f"{api_url}/scenes/{scene_id}",
        timeout=60,
    )

    if not response.ok:

        raise RuntimeError(
            f"Scene deletion failed "
            f"({response.status_code}): "
            f"{api_error_message(response)}"
        )

    try:

        return response.json()

    except ValueError:

        return {
            "message": response.text,
        }


def export_editor_video(
    api_url: str,
    video_id: int,
) -> dict[str, Any]:

    response = requests.post(
        f"{api_url}/export/{video_id}",
        timeout=1800,
    )

    if not response.ok:

        raise RuntimeError(
            f"Export failed "
            f"({response.status_code}): "
            f"{api_error_message(response)}"
        )

    return response.json()


# ============================================================
# AI SCENE HELPERS
# ============================================================

def new_scene() -> dict[str, Any]:

    return {
        "narration": "",
        "visual_prompt": "",
        "voice": "Auto",
    }


def reset_scenes() -> None:

    st.session_state.scenes = [
        {
            "narration": (
                "Solar energy comes from sunlight."
            ),
            "visual_prompt": (
                "Solar panels receiving morning sunlight "
                "on a modern rooftop."
            ),
            "voice": "Female",
        }
    ]

    for key in list(st.session_state.keys()):

        if (
            key.startswith("narration_")
            or key.startswith("visual_")
            or key.startswith("voice_")
        ):
            del st.session_state[key]


def remove_scene(
    index: int,
) -> None:

    if len(st.session_state.scenes) <= 1:

        st.warning(
            "At least one scene is required."
        )

        return

    st.session_state.scenes.pop(index)


def get_scene_value(
    index: int,
    field: str,
    default: str = "",
) -> str:

    key = f"{field}_{index}"

    value = st.session_state.get(
        key,
        default,
    )

    if value is None:
        return ""

    return str(value)


def sync_scenes_from_widgets() -> None:

    for index, scene in enumerate(
        st.session_state.scenes
    ):

        scene["narration"] = get_scene_value(
            index,
            "narration",
            scene.get("narration", ""),
        )

        scene["visual_prompt"] = get_scene_value(
            index,
            "visual",
            scene.get("visual_prompt", ""),
        )

        scene["voice"] = get_scene_value(
            index,
            "voice",
            scene.get("voice", "Auto"),
        )


# ============================================================
# EDITOR RESPONSE HELPERS
# ============================================================

def get_editor_scenes(
    editor_data: dict[str, Any],
) -> list[dict[str, Any]]:

    scenes = editor_data.get(
        "scenes",
        [],
    )

    if not isinstance(scenes, list):
        return []

    return scenes


def get_scene_timeline(
    scene: dict[str, Any],
) -> dict[str, Any]:

    timeline = scene.get(
        "timeline",
        {},
    )

    if isinstance(timeline, dict):
        return timeline

    return {}


def get_scene_assets(
    scene: dict[str, Any],
) -> list[dict[str, Any]]:

    assets = scene.get(
        "assets",
        [],
    )

    if isinstance(assets, list):
        return assets

    return []


def get_editor_scene_id(
    scene: dict[str, Any],
) -> int | None:

    """
    Current backend:
        "scene_id": 10
    """

    scene_id = scene.get(
        "scene_id"
    )

    if scene_id is None:
        scene_id = scene.get(
            "id"
        )

    if scene_id is None:
        return None

    try:
        return int(scene_id)

    except (
        TypeError,
        ValueError,
    ):
        return None


def find_asset_url(
    api_url: str,
    assets: list[dict[str, Any]],
    asset_type: str,
) -> str | None:
    """
    Current backend asset format:

        {
            "id": 28,
            "type": "image",
            "url": "/media/images/example.png"
        }

    Older format is also supported.
    """

    for asset in assets:

        actual_type = (
            asset.get("type")
            or asset.get("asset_type")
        )

        actual_url = (
            asset.get("url")
            or asset.get("file_url")
        )

        if actual_type == asset_type:

            return make_absolute_url(
                api_url,
                actual_url,
            )

    return None


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# AUDIO DURATION CACHE
# ============================================================

def get_cached_audio_duration(
    api_url: str,
    scene: dict[str, Any],
) -> float | None:
    """
    Cache audio duration per editor scene.

    This avoids repeatedly running ffprobe during
    Streamlit reruns.
    """

    scene_id = get_editor_scene_id(
        scene
    )

    if scene_id is None:
        return None

    cache_key = (
        f"audio_duration_{scene_id}"
    )

    if cache_key in st.session_state:

        cached = st.session_state[
            cache_key
        ]

        if cached is None:
            return None

        return float(cached)

    assets = get_scene_assets(
        scene
    )

    audio_url = find_asset_url(
        api_url,
        assets,
        "audio",
    )

    duration = get_audio_duration(
        api_url,
        audio_url,
    )

    st.session_state[
        cache_key
    ] = duration

    return duration


# ============================================================
# TIMELINE CALCULATION
# ============================================================

def calculate_timeline_from_scene_durations(
    editor_scenes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Calculate contiguous timeline positions.

    Scene durations are respected exactly.
    """

    timeline_rows = []

    current_time = 0.0

    for index, scene in enumerate(
        editor_scenes
    ):

        scene_id = get_editor_scene_id(
            scene
        )

        duration = safe_float(
            scene.get(
                "duration"
            ),
            0.1,
        )

        if duration <= 0:
            duration = 0.1

        timeline = get_scene_timeline(
            scene
        )

        transition = timeline.get(
            "transition"
        )

        text_overlay = timeline.get(
            "text_overlay"
        )

        start_time = current_time

        end_time = (
            current_time
            + duration
        )

        timeline_rows.append(
            {
                "scene_id": scene_id,
                "order": index + 1,
                "duration": duration,
                "start_time": start_time,
                "end_time": end_time,
                "transition": transition,
                "text_overlay": text_overlay,
            }
        )

        current_time = end_time

    return timeline_rows


# ============================================================
# SAVE SCENE + REBUILD TIMELINE
# ============================================================

def save_scene_and_rebuild_timeline(
    api_url: str,
    editor_data: dict[str, Any],
    changed_scene_id: int,
    duration: float,
    text_overlay: str | None,
    transition: str | None,
) -> dict[str, Any]:
    """
    Save the selected scene and recalculate all timeline
    start/end positions.

    Narration protection:
        requested duration must never be shorter than
        the scene's actual narration duration.
    """

    video_id = int(
        editor_data["video"]["id"]
    )

    editor_scenes = get_editor_scenes(
        editor_data
    )

    working_scenes = []

    for original_scene in editor_scenes:

        scene = dict(
            original_scene
        )

        scene["timeline"] = dict(
            get_scene_timeline(
                original_scene
            )
        )

        working_scenes.append(
            scene
        )

    target_found = False

    for scene in working_scenes:

        scene_id = get_editor_scene_id(
            scene
        )

        if scene_id == changed_scene_id:

            # ----------------------------------------------
            # Get actual narration duration.
            # ----------------------------------------------

            audio_duration = (
                get_cached_audio_duration(
                    api_url,
                    scene,
                )
            )

            # ----------------------------------------------
            # Never allow scene duration to become shorter
            # than the narration.
            # ----------------------------------------------

            if (
                audio_duration is not None
                and duration < audio_duration
            ):

                raise ValueError(
                    f"Scene narration is "
                    f"{audio_duration:.2f}s long. "
                    f"Scene duration cannot be "
                    f"shorter than the narration."
                )

            scene["duration"] = float(
                duration
            )

            scene["timeline"][
                "text_overlay"
            ] = text_overlay

            scene["timeline"][
                "transition"
            ] = transition

            target_found = True

            break

    if not target_found:

        raise RuntimeError(
            f"Scene {changed_scene_id} "
            "was not found in the editor."
        )

    working_scenes.sort(
        key=lambda scene: safe_float(
            scene.get(
                "order"
            ),
            0,
        )
    )

    timeline_rows = (
        calculate_timeline_from_scene_durations(
            working_scenes
        )
    )

    # ----------------------------------------------
    # Update every scene so timeline stays contiguous.
    # ----------------------------------------------

    for row in timeline_rows:

        scene_id = row[
            "scene_id"
        ]

        if scene_id is None:
            continue

        update_editor_scene(
            api_url=api_url,
            video_id=video_id,
            scene_id=int(
                scene_id
            ),
            payload={
                "duration": row[
                    "duration"
                ],
                "start_time": row[
                    "start_time"
                ],
                "end_time": row[
                    "end_time"
                ],
                "text_overlay": row[
                    "text_overlay"
                ],
                "transition": row[
                    "transition"
                ],
            },
        )

    return get_editor_data(
        api_url,
        video_id,
    )


# ============================================================
# REBUILD TIMELINE
# ============================================================

def rebuild_editor_timeline(
    api_url: str,
    editor_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Recalculate timeline positions using the durations that
    are already stored in the editor.

    Narration protection:
        If a stored scene duration is a little shorter than
        the actual narration duration, automatically extend
        the scene duration to the narration duration instead
        of failing the reorder/delete operation.
    """

    video_id = int(
        editor_data["video"]["id"]
    )

    editor_scenes = get_editor_scenes(
        editor_data
    )

    # ------------------------------------------------------------
    # IMPORTANT:
    # Protect every scene BEFORE calculating the timeline.
    #
    # Example:
    #     stored duration  = 5.58
    #     narration        = 5.59
    #
    # We use 5.59 automatically. This prevents a tiny
    # ffprobe/database rounding difference from breaking
    # Move Up, Move Down, Apply Order, or Delete.
    # ------------------------------------------------------------

    protected_scenes = []

    for original_scene in editor_scenes:

        scene = dict(
            original_scene
        )

        scene["timeline"] = dict(
            get_scene_timeline(
                original_scene
            )
        )

        current_duration = safe_float(
            scene.get(
                "duration"
            ),
            0.1,
        )

        if current_duration <= 0:
            current_duration = 0.1

        audio_duration = (
            get_cached_audio_duration(
                api_url,
                scene,
            )
        )

        if audio_duration is not None:

            # Add a tiny safety margin so floating-point/ffprobe
            # rounding cannot make the scene appear shorter than
            # the narration again.
            safe_narration_duration = (
                float(audio_duration) + 0.01
            )

            current_duration = max(
                current_duration,
                safe_narration_duration,
            )

        scene["duration"] = current_duration

        protected_scenes.append(
            scene
        )

    # ------------------------------------------------------------
    # Recalculate the complete contiguous timeline AFTER all
    # narration-safe durations have been applied.
    # ------------------------------------------------------------

    timeline_rows = (
        calculate_timeline_from_scene_durations(
            protected_scenes
        )
    )

    for row in timeline_rows:

        scene_id = row[
            "scene_id"
        ]

        if scene_id is None:
            continue

        update_editor_scene(
            api_url=api_url,
            video_id=video_id,
            scene_id=int(scene_id),
            payload={
                "duration": row[
                    "duration"
                ],
                "start_time": row[
                    "start_time"
                ],
                "end_time": row[
                    "end_time"
                ],
                "text_overlay": row[
                    "text_overlay"
                ],
                "transition": row[
                    "transition"
                ],
            },
        )

    return get_editor_data(
        api_url,
        video_id,
    )


# ============================================================
# SESSION STATE
# ============================================================

if "scenes" not in st.session_state:
    reset_scenes()

if "result" not in st.session_state:
    st.session_state.result = None

if "editor_data" not in st.session_state:
    st.session_state.editor_data = None

if "export_result" not in st.session_state:
    st.session_state.export_result = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## frameforge")

    st.caption("AI video studio")

    st.divider()

    api_url = st.text_input(
        "FastAPI base URL",
        value=os.getenv(
            "BASE_URL",
            "http://127.0.0.1:8001",
        ),
        help=(
            "The URL where app.main:app "
            "is running."
        ),
    ).strip().rstrip("/")

    st.markdown("### Workflow")

    st.markdown(
        "1. Write your scenes\n"
        "2. Choose a voice\n"
        "3. Generate the project\n"
        "4. Edit duration and narration\n"
        "5. Add text and transitions\n"
        "6. Reorder scenes\n"
        "7. Export the final video"
    )

    st.divider()

    if st.button(
        "Reset scenes",
        use_container_width=True,
    ):

        reset_scenes()

        st.session_state.result = None
        st.session_state.editor_data = None
        st.session_state.export_result = None

        # Clear cached audio durations.
        for key in list(
            st.session_state.keys()
        ):
            if key.startswith(
                "audio_duration_"
            ):
                del st.session_state[key]

        st.rerun()


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    '<p class="eyebrow">AI video studio / 01</p>',
    unsafe_allow_html=True,
)

st.markdown(
    "# Turn a script into<br><em>something you can see.</em>",
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="lede">'
    "Create scenes with AI, preview the generated media, "
    "then edit narration-safe duration, text, transitions "
    "and ordering before exporting."
    "</p>",
    unsafe_allow_html=True,
)

st.write("")


# ============================================================
# PROJECT SETUP
# ============================================================

st.markdown(
    "## 01  Project setup"
)

project_id = st.text_input(
    "Project name",
    value="my-first-film",
    key="project_id",
)


# ============================================================
# AI SCENES
# ============================================================

st.markdown(
    "## 02  AI scenes"
)

st.caption(
    f"{len(st.session_state.scenes)} "
    f"scene(s) in your project"
)


# ============================================================
# AI INPUT SCENES
# ============================================================

for index, scene in enumerate(
    st.session_state.scenes
):

    with st.container(
        border=True
    ):

        header_left, header_right = (
            st.columns([5, 1])
        )

        with header_left:

            st.markdown(
                f"### Scene {index + 1:02d}"
            )

        with header_right:

            if len(
                st.session_state.scenes
            ) > 1:

                if st.button(
                    "Remove",
                    key=(
                        f"remove_scene_"
                        f"{index}"
                    ),
                    use_container_width=True,
                ):

                    sync_scenes_from_widgets()

                    remove_scene(
                        index
                    )

                    st.rerun()

        narration = st.text_area(
            "Narration",
            value=scene.get(
                "narration",
                "",
            ),
            placeholder=(
                "What should the audience hear?"
            ),
            key=f"narration_{index}",
            height=120,
        )

        scene["narration"] = (
            narration
        )

        visual_prompt = st.text_area(
            "Visual direction",
            value=scene.get(
                "visual_prompt",
                "",
            ),
            placeholder=(
                "Describe the image and atmosphere..."
            ),
            key=f"visual_{index}",
            height=120,
        )

        scene["visual_prompt"] = (
            visual_prompt
        )

        voice_options = [
            "Auto",
            "Female",
            "Male",
        ]

        current_voice = scene.get(
            "voice",
            "Auto",
        )

        if (
            current_voice
            not in voice_options
        ):
            current_voice = "Auto"

        selected_voice = st.radio(
            "Voice direction",
            voice_options,
            index=voice_options.index(
                current_voice
            ),
            horizontal=True,
            key=f"voice_{index}",
        )

        scene["voice"] = (
            selected_voice
        )


# ============================================================
# ADD SCENE
# ============================================================

st.write("")

add_scene_col, spacer_col = (
    st.columns([2, 8])
)

with add_scene_col:

    if st.button(
        "+ Add scene",
        use_container_width=True,
    ):

        sync_scenes_from_widgets()

        st.session_state.scenes.append(
            new_scene()
        )

        st.rerun()


# ============================================================
# GENERATE PROJECT
# ============================================================

st.divider()

st.markdown(
    "### Generate"
)

generate_clicked = st.button(
    "Generate project ↗",
    type="primary",
    use_container_width=True,
)


# ============================================================
# GENERATE HANDLER
# ============================================================

if generate_clicked:

    sync_scenes_from_widgets()

    if not project_id.strip():

        st.error(
            "Enter a project name before generating."
        )

    else:

        incomplete_scenes = []

        for index, scene in enumerate(
            st.session_state.scenes
        ):

            narration = scene.get(
                "narration",
                "",
            ).strip()

            visual_prompt = scene.get(
                "visual_prompt",
                "",
            ).strip()

            missing_fields = []

            if not narration:
                missing_fields.append(
                    "narration"
                )

            if not visual_prompt:
                missing_fields.append(
                    "visual direction"
                )

            if missing_fields:

                incomplete_scenes.append(
                    f"Scene {index + 1}: "
                    + " and ".join(
                        missing_fields
                    )
                )

        if incomplete_scenes:

            st.error(
                "Please complete these scenes:\n\n"
                + "\n".join(
                    f"• {item}"
                    for item in incomplete_scenes
                )
            )

        else:

            request_scenes = []

            for index, scene in enumerate(
                st.session_state.scenes
            ):

                voice_value = scene.get(
                    "voice",
                    "Auto",
                )

                if voice_value not in [
                    "Auto",
                    "Female",
                    "Male",
                ]:
                    voice_value = "Auto"

                request_scenes.append(
                    {
                        "scene_id": (
                            index + 1
                        ),
                        "narration": scene[
                            "narration"
                        ].strip(),
                        "visual_prompt": scene[
                            "visual_prompt"
                        ].strip(),
                        "voice": (
                            None
                            if voice_value
                            == "Auto"
                            else voice_value.lower()
                        ),
                    }
                )

            st.info(
                f"Connecting to FastAPI: "
                f"{api_url}"
            )

            with st.spinner(
                "Generating audio, images, scene videos "
                "and final video..."
            ):

                try:

                    response = requests.post(
                        (
                            f"{api_url}"
                            "/api/v1/projects/generate"
                        ),
                        json={
                            "project_id": (
                                project_id.strip()
                            ),
                            "scenes": (
                                request_scenes
                            ),
                        },
                        timeout=1800,
                    )

                    if not response.ok:

                        raise requests.HTTPError(
                            response=response
                        )

                    api_result = (
                        response.json()
                    )

                    st.session_state.result = (
                        api_result
                    )

                    generated_video_id = (
                        api_result.get(
                            "video_id"
                        )
                    )

                    if (
                        generated_video_id
                        is not None
                    ):

                        st.session_state.editor_data = (
                            get_editor_data(
                                api_url,
                                int(
                                    generated_video_id
                                ),
                            )
                        )

                    st.session_state.export_result = (
                        None
                    )

                    st.success(
                        "Project generated successfully "
                        "and the editor was loaded."
                    )

                    st.rerun()

                except (
                    requests.exceptions.ConnectionError
                ):

                    st.error(
                        "Could not connect to FastAPI.\n\n"
                        f"Make sure FastAPI is running at:\n"
                        f"{api_url}"
                    )

                except (
                    requests.exceptions.Timeout
                ):

                    st.error(
                        "The media API took too long "
                        "to respond."
                    )

                except requests.exceptions.HTTPError as exc:

                    response_obj = (
                        exc.response
                    )

                    status_code = (
                        response_obj.status_code
                        if response_obj is not None
                        else "unknown"
                    )

                    detail = (
                        api_error_message(
                            response_obj
                        )
                        if response_obj is not None
                        else str(exc)
                    )

                    st.error(
                        f"Media API error "
                        f"({status_code}): "
                        f"{detail}"
                    )

                except RuntimeError as exc:

                    st.error(
                        str(exc)
                    )

                except requests.RequestException as exc:

                    st.error(
                        f"Could not reach the media API: "
                        f"{exc}"
                    )

                except ValueError:

                    st.error(
                        "The media API returned "
                        "invalid JSON."
                    )


# ============================================================
# GENERATED RESULTS
# ============================================================

if st.session_state.result:

    result = st.session_state.result

    st.divider()

    st.markdown(
        f"## 03  Generated project · "
        f"`{result.get('project_id', 'unknown')}`"
    )

    video_id = result.get(
        "video_id"
    )

    if video_id is not None:

        st.markdown(
            f'<span class="status-pill">'
            f"Editor Video ID: {video_id}"
            f"</span>",
            unsafe_allow_html=True,
        )

    st.write("")

    # ========================================================
    # FIRST CUT
    # ========================================================

    final_video_url = make_absolute_url(
        api_url,
        result.get(
            "final_video_url"
        ),
    )

    if not final_video_url:

        final_video_url = make_absolute_url(
            api_url,
            result.get(
                "final_video_path"
            ),
        )

    if final_video_url:

        with st.container(
            border=True
        ):

            st.markdown(
                "### 🎬 AI-generated first cut"
            )

            st.caption(
                "Automatically generated before editing."
            )

            st.video(
                final_video_url
            )

            st.link_button(
                "Open first-cut video ↗",
                final_video_url,
                use_container_width=True,
            )


    # ========================================================
    # INDIVIDUAL GENERATED SCENES
    # ========================================================

    st.markdown(
        "### Individual generated scenes"
    )

    generated_scenes = result.get(
        "scenes",
        [],
    )

    if not generated_scenes:

        st.warning(
            "No individual scenes were returned."
        )

    else:

        number_of_columns = min(
            3,
            max(
                1,
                len(
                    generated_scenes
                ),
            ),
        )

        columns = st.columns(
            number_of_columns
        )

        for index, scene in enumerate(
            generated_scenes
        ):

            with columns[
                index % len(columns)
            ]:

                st.markdown(
                    '<div class="result-card">',
                    unsafe_allow_html=True,
                )

                scene_number = scene.get(
                    "scene_id",
                    index + 1,
                )

                st.markdown(
                    f"### Scene "
                    f"{scene_number:02d}"
                )

                image_url = make_absolute_url(
                    api_url,
                    scene.get(
                        "image_url"
                    )
                    or scene.get(
                        "image_path"
                    ),
                )

                if image_url:

                    st.image(
                        image_url,
                        use_container_width=True,
                    )

                audio_url = make_absolute_url(
                    api_url,
                    scene.get(
                        "audio_url"
                    )
                    or scene.get(
                        "audio_path"
                    ),
                )

                if audio_url:

                    st.audio(
                        audio_url
                    )

                video_url = make_absolute_url(
                    api_url,
                    scene.get(
                        "video_url"
                    )
                    or scene.get(
                        "video_path"
                    ),
                )

                if video_url:

                    st.video(
                        video_url
                    )

                    st.link_button(
                        "Open scene video ↗",
                        video_url,
                        use_container_width=True,
                    )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True,
                )


# ============================================================
# VIDEO EDITOR
# ============================================================

if (
    st.session_state.editor_data
    and st.session_state.result
):

    editor_data = (
        st.session_state.editor_data
    )

    editor_video = (
        editor_data.get(
            "video",
            {},
        )
    )

    editor_scenes = (
        get_editor_scenes(
            editor_data
        )
    )

    if editor_scenes:

        st.divider()

        st.markdown(
            "## 04  Video editor"
        )

        st.caption(
            "Edit duration, narration-safe timing, "
            "text overlays, transitions and scene order."
        )


        # ====================================================
        # SUMMARY
        # ====================================================

        summary_col1, summary_col2, summary_col3 = (
            st.columns(3)
        )

        with summary_col1:

            st.metric(
                "Video ID",
                editor_video.get(
                    "id",
                    "-",
                ),
            )

        with summary_col2:

            st.metric(
                "Scenes",
                len(editor_scenes),
            )

        with summary_col3:

            total_duration = safe_float(
                editor_video.get(
                    "total_duration",
                    0,
                )
            )

            st.metric(
                "Duration",
                f"{total_duration:.2f}s",
            )


        # ====================================================
        # TIMELINE
        # ====================================================

        st.markdown(
            "### Timeline"
        )

        timeline_rows = (
            calculate_timeline_from_scene_durations(
                editor_scenes
            )
        )

        timeline_html = (
            '<div class="timeline-track">'
        )

        for row in timeline_rows:

            timeline_html += (
                '<div class="timeline-item">'
                f"<strong>"
                f"Scene {row['order']}"
                f"</strong>"
                f"<small>"
                f"{row['start_time']:.2f}s "
                f"→ "
                f"{row['end_time']:.2f}s"
                f"</small>"
                "<br>"
                f"<small>"
                f"Duration: "
                f"{row['duration']:.2f}s"
                f"</small>"
                "</div>"
            )

        timeline_html += (
            "</div>"
        )

        st.markdown(
            timeline_html,
            unsafe_allow_html=True,
        )


        # ====================================================
        # EDIT SCENES
        # ====================================================

        st.markdown(
            "### Edit scenes"
        )

        for index, scene in enumerate(
            editor_scenes
        ):

            scene_id = get_editor_scene_id(
                scene
            )

            if scene_id is None:

                st.error(
                    f"Could not identify "
                    f"Scene {index + 1}."
                )

                continue

            scene_order = int(
                safe_float(
                    scene.get(
                        "order",
                        index + 1,
                    ),
                    index + 1,
                )
            )

            scene_title = scene.get(
                "title",
                f"Scene {scene_order}",
            )

            current_duration = safe_float(
                scene.get(
                    "duration",
                    5.0,
                ),
                5.0,
            )

            timeline = get_scene_timeline(
                scene
            )

            assets = get_scene_assets(
                scene
            )

            current_text = timeline.get(
                "text_overlay"
            )

            if current_text is None:
                current_text = ""

            current_transition = timeline.get(
                "transition"
            )

            if not current_transition:
                current_transition = "none"

            # =================================================
            # AVAILABLE TRANSITIONS
            # =================================================

            transition_options = [
                "none",
                "fade",
                "fade_in",
                "fade_out",
                "crossfade",
                "wipe_left",
                "wipe_right",
                "wipe_up",
                "wipe_down",
                "slide_left",
                "slide_right",
                "slide_up",
                "slide_down",
                "zoom_in",
                "zoom_out",
                "blur",
            ]

            if (
                current_transition
                not in transition_options
            ):
                current_transition = "none"


            # =================================================
            # GET NARRATION DURATION
            # =================================================

            narration_duration = (
                get_cached_audio_duration(
                    api_url,
                    scene,
                )
            )

            if narration_duration is not None:

                minimum_duration = max(
                    0.1,
                    narration_duration,
                )

                # Existing database duration might already
                # be smaller than the audio. Never present
                # a smaller default to the user.
                displayed_duration = max(
                    current_duration,
                    minimum_duration,
                )

            else:

                minimum_duration = 0.1

                displayed_duration = max(
                    0.1,
                    current_duration,
                )


            # =================================================
            # SCENE CARD
            # =================================================

            with st.container(
                border=True
            ):

                st.markdown(
                    '<div class="scene-number">'
                    f"Scene {scene_order:02d}"
                    "</div>",
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f'<div class="editor-heading">'
                    f"{scene_title}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                st.caption(
                    f"Scene ID: {scene_id}"
                )

                editor_left, editor_right = (
                    st.columns(
                        [1.15, 1.85]
                    )
                )


                # =============================================
                # MEDIA PREVIEW
                # =============================================

                with editor_left:

                    video_url = find_asset_url(
                        api_url,
                        assets,
                        "video",
                    )

                    image_url = find_asset_url(
                        api_url,
                        assets,
                        "image",
                    )

                    audio_url = find_asset_url(
                        api_url,
                        assets,
                        "audio",
                    )

                    if video_url:

                        st.video(
                            video_url
                        )

                    elif image_url:

                        st.image(
                            image_url,
                            use_container_width=True,
                        )

                    else:

                        st.info(
                            "No visual asset available."
                        )

                    if audio_url:

                        st.audio(
                            audio_url
                        )


                # =============================================
                # EDITING CONTROLS
                # =============================================

                with editor_right:

                    st.markdown(
                        "#### Scene settings"
                    )

                    # -----------------------------------------
                    # NARRATION INFORMATION
                    # -----------------------------------------

                    if narration_duration is not None:

                        st.markdown(
                            '<div class="editor-info">'
                            f"<b>Narration duration:</b> "
                            f"{narration_duration:.2f}s"
                            "<br>"
                            f"<b>Minimum scene duration:</b> "
                            f"{narration_duration:.2f}s"
                            "</div>",
                            unsafe_allow_html=True,
                        )

                    else:

                        st.caption(
                            "Narration duration could not be "
                            "measured locally. The backend "
                            "will still protect the narration "
                            "during export."
                        )


                    # -----------------------------------------
                    # DURATION
                    # -----------------------------------------

                    duration_value = st.number_input(
                        "Duration (seconds)",
                        min_value=float(
                            minimum_duration
                        ),
                        max_value=3600.0,
                        value=float(
                            displayed_duration
                        ),
                        step=0.1,
                        key=(
                            f"duration_"
                            f"{scene_id}"
                        ),
                        help=(
                            "The scene cannot be shorter "
                            "than its narration."
                        ),
                    )


                    # -----------------------------------------
                    # TEXT OVERLAY
                    # -----------------------------------------

                    text_value = st.text_area(
                        "Text overlay",
                        value=str(
                            current_text
                        ),
                        placeholder=(
                            "Enter text to display "
                            "on this scene..."
                        ),
                        height=100,
                        key=(
                            f"text_"
                            f"{scene_id}"
                        ),
                    )


                    # -----------------------------------------
                    # TRANSITION
                    # -----------------------------------------

                    transition_labels = {
                        "none": "None",
                        "fade": "Fade",
                        "fade_in": "Fade In",
                        "fade_out": "Fade Out",
                        "crossfade": "Crossfade",
                        "wipe_left": "Wipe Left",
                        "wipe_right": "Wipe Right",
                        "wipe_up": "Wipe Up",
                        "wipe_down": "Wipe Down",
                        "slide_left": "Slide Left",
                        "slide_right": "Slide Right",
                        "slide_up": "Slide Up",
                        "slide_down": "Slide Down",
                        "zoom_in": "Zoom In",
                        "zoom_out": "Zoom Out",
                        "blur": "Blur",
                    }

                    transition_value = st.selectbox(
                        "Transition",
                        transition_options,
                        index=transition_options.index(
                            current_transition
                        ),
                        format_func=(
                            lambda value: transition_labels.get(
                                value,
                                value,
                            )
                        ),
                        key=(
                            f"transition_"
                            f"{scene_id}"
                        ),
                        help=(
                            "Choose the visual transition/effect "
                            "used when this scene is rendered."
                        ),
                    )


                    st.caption(
                        "Fade, crossfade, wipes, slides, "
                        "zoom and blur are available. "
                        "Crossfade is applied between adjacent scenes."
                    )

                    # -----------------------------------------
                    # VALIDATION
                    # -----------------------------------------

                    duration_is_valid = True

                    if (
                        narration_duration is not None
                        and duration_value
                        < narration_duration
                    ):

                        duration_is_valid = False

                        st.error(
                            f"Duration must be at least "
                            f"{narration_duration:.2f}s "
                            f"because of the narration."
                        )


                    # -----------------------------------------
                    # CURRENT TIMELINE
                    # -----------------------------------------

                    current_start = safe_float(
                        timeline.get(
                            "start_time",
                            0,
                        )
                    )

                    current_end = safe_float(
                        timeline.get(
                            "end_time",
                            current_start
                            + current_duration,
                        )
                    )

                    st.markdown(
                        '<div class="editor-info">'
                        f"<b>Current timeline:</b><br>"
                        f"{current_start:.2f}s "
                        f"→ "
                        f"{current_end:.2f}s"
                        "</div>",
                        unsafe_allow_html=True,
                    )


                    # -----------------------------------------
                    # SAVE
                    # -----------------------------------------

                    if st.button(
                        "Save scene changes",
                        key=(
                            f"save_"
                            f"{scene_id}"
                        ),
                        type="primary",
                        use_container_width=True,
                        disabled=(
                            not duration_is_valid
                        ),
                    ):

                        selected_transition = (
                            None
                            if transition_value
                            == "none"
                            else transition_value
                        )

                        selected_text = (
                            text_value.strip()
                            or None
                        )

                        try:

                            # -----------------------------
                            # Final frontend validation
                            # -----------------------------

                            if (
                                narration_duration
                                is not None
                                and duration_value
                                < narration_duration
                            ):

                                raise ValueError(
                                    f"Scene duration "
                                    f"({duration_value:.2f}s) "
                                    f"cannot be shorter than "
                                    f"narration "
                                    f"({narration_duration:.2f}s)."
                                )

                            with st.spinner(
                                f"Saving {scene_title}..."
                            ):

                                fresh_data = (
                                    save_scene_and_rebuild_timeline(
                                        api_url=api_url,
                                        editor_data=editor_data,
                                        changed_scene_id=int(
                                            scene_id
                                        ),
                                        duration=float(
                                            duration_value
                                        ),
                                        text_overlay=(
                                            selected_text
                                        ),
                                        transition=(
                                            selected_transition
                                        ),
                                    )
                                )

                                st.session_state.editor_data = (
                                    fresh_data
                                )

                                st.session_state.export_result = (
                                    None
                                )

                            st.success(
                                f"{scene_title} "
                                "updated successfully."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                f"Could not save "
                                f"{scene_title}: "
                                f"{exc}"
                            )


                # =================================================
                # REORDER + DELETE CONTROLS
                # =================================================

                st.write("")

                (
                    up_col,
                    down_col,
                    position_col,
                    apply_col,
                    delete_col,
                ) = st.columns(
                    [1, 1, 1.4, 1.2, 1.2]
                )

                # -------------------------------------------------
                # MOVE UP
                # -------------------------------------------------

                with up_col:

                    if index > 0:

                        if st.button(
                            "↑ Move up",
                            key=(
                                f"move_up_"
                                f"{scene_id}"
                            ),
                            use_container_width=True,
                        ):

                            try:

                                current_scene_ids = [
                                    get_editor_scene_id(
                                        item
                                    )
                                    for item in editor_scenes
                                ]

                                current_scene_ids = [
                                    int(value)
                                    for value in current_scene_ids
                                    if value is not None
                                ]

                                if (
                                    len(current_scene_ids)
                                    != len(editor_scenes)
                                ):

                                    raise RuntimeError(
                                        "Could not determine "
                                        "all scene IDs."
                                    )

                                (
                                    current_scene_ids[
                                        index - 1
                                    ],
                                    current_scene_ids[
                                        index
                                    ],
                                ) = (
                                    current_scene_ids[
                                        index
                                    ],
                                    current_scene_ids[
                                        index - 1
                                    ],
                                )

                                reorder_editor_scenes(
                                    api_url=api_url,
                                    video_id=int(
                                        editor_video[
                                            "id"
                                        ]
                                    ),
                                    scene_ids=(
                                        current_scene_ids
                                    ),
                                )

                                fresh_data = (
                                    get_editor_data(
                                        api_url,
                                        int(
                                            editor_video[
                                                "id"
                                            ]
                                        ),
                                    )
                                )

                                fresh_data = (
                                    rebuild_editor_timeline(
                                        api_url,
                                        fresh_data,
                                    )
                                )

                                st.session_state.editor_data = (
                                    fresh_data
                                )

                                st.success(
                                    "Scene moved up."
                                )

                                st.rerun()

                            except Exception as exc:

                                st.error(
                                    f"Could not move "
                                    f"scene up: {exc}"
                                )

                # -------------------------------------------------
                # MOVE DOWN
                # -------------------------------------------------

                with down_col:

                    if (
                        index
                        < len(editor_scenes) - 1
                    ):

                        if st.button(
                            "↓ Move down",
                            key=(
                                f"move_down_"
                                f"{scene_id}"
                            ),
                            use_container_width=True,
                        ):

                            try:

                                current_scene_ids = [
                                    get_editor_scene_id(
                                        item
                                    )
                                    for item in editor_scenes
                                ]

                                current_scene_ids = [
                                    int(value)
                                    for value in current_scene_ids
                                    if value is not None
                                ]

                                if (
                                    len(current_scene_ids)
                                    != len(editor_scenes)
                                ):

                                    raise RuntimeError(
                                        "Could not determine "
                                        "all scene IDs."
                                    )

                                (
                                    current_scene_ids[
                                        index
                                    ],
                                    current_scene_ids[
                                        index + 1
                                    ],
                                ) = (
                                    current_scene_ids[
                                        index + 1
                                    ],
                                    current_scene_ids[
                                        index
                                    ],
                                )

                                reorder_editor_scenes(
                                    api_url=api_url,
                                    video_id=int(
                                        editor_video[
                                            "id"
                                        ]
                                    ),
                                    scene_ids=(
                                        current_scene_ids
                                    ),
                                )

                                fresh_data = (
                                    get_editor_data(
                                        api_url,
                                        int(
                                            editor_video[
                                                "id"
                                            ]
                                        ),
                                    )
                                )

                                fresh_data = (
                                    rebuild_editor_timeline(
                                        api_url,
                                        fresh_data,
                                    )
                                )

                                st.session_state.editor_data = (
                                    fresh_data
                                )

                                st.success(
                                    "Scene moved down."
                                )

                                st.rerun()

                            except Exception as exc:

                                st.error(
                                    f"Could not move "
                                    f"scene down: {exc}"
                                )

                # -------------------------------------------------
                # SELECT SCENE POSITION
                # -------------------------------------------------

                with position_col:

                    position_options = list(
                        range(
                            1,
                            len(editor_scenes) + 1,
                        )
                    )

                    selected_position = st.selectbox(
                        "Position",
                        position_options,
                        index=scene_order - 1,
                        key=(
                            f"position_"
                            f"{scene_id}"
                        ),
                        format_func=(
                            lambda value: (
                                f"Position {value}"
                            )
                        ),
                    )

                # -------------------------------------------------
                # APPLY SELECTED POSITION
                # -------------------------------------------------

                with apply_col:

                    if st.button(
                        "Apply order",
                        key=(
                            f"apply_order_"
                            f"{scene_id}"
                        ),
                        use_container_width=True,
                    ):

                        try:

                            current_scene_ids = [
                                get_editor_scene_id(
                                    item
                                )
                                for item in editor_scenes
                            ]

                            current_scene_ids = [
                                int(value)
                                for value in current_scene_ids
                                if value is not None
                            ]

                            if (
                                len(current_scene_ids)
                                != len(editor_scenes)
                            ):

                                raise RuntimeError(
                                    "Could not determine "
                                    "all scene IDs."
                                )

                            current_index = (
                                current_scene_ids.index(
                                    int(scene_id)
                                )
                            )

                            target_index = (
                                int(selected_position) - 1
                            )

                            if (
                                current_index
                                != target_index
                            ):

                                moved_scene_id = (
                                    current_scene_ids.pop(
                                        current_index
                                    )
                                )

                                current_scene_ids.insert(
                                    target_index,
                                    moved_scene_id,
                                )

                                reorder_editor_scenes(
                                    api_url=api_url,
                                    video_id=int(
                                        editor_video[
                                            "id"
                                        ]
                                    ),
                                    scene_ids=(
                                        current_scene_ids
                                    ),
                                )

                            fresh_data = (
                                get_editor_data(
                                    api_url,
                                    int(
                                        editor_video[
                                            "id"
                                        ]
                                    ),
                                )
                            )

                            fresh_data = (
                                rebuild_editor_timeline(
                                    api_url,
                                    fresh_data,
                                )
                            )

                            st.session_state.editor_data = (
                                fresh_data
                            )

                            st.success(
                                f"{scene_title} moved to "
                                f"position "
                                f"{selected_position}."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                f"Could not reorder "
                                f"{scene_title}: {exc}"
                            )

                # -------------------------------------------------
                # DELETE SCENE
                # -------------------------------------------------

                with delete_col:

                    delete_disabled = (
                        len(editor_scenes) <= 1
                    )

                    if st.button(
                        "🗑 Delete",
                        key=(
                            f"delete_editor_scene_"
                            f"{scene_id}"
                        ),
                        use_container_width=True,
                        disabled=delete_disabled,
                    ):

                        try:

                            if len(editor_scenes) <= 1:

                                raise RuntimeError(
                                    "At least one scene "
                                    "must remain."
                                )

                            video_id = int(
                                editor_video[
                                    "id"
                                ]
                            )

                            with st.spinner(
                                f"Deleting {scene_title}..."
                            ):

                                delete_editor_scene(
                                    api_url=api_url,
                                    scene_id=int(
                                        scene_id
                                    ),
                                )

                                # Remove stale audio-duration
                                # cache for the deleted scene.
                                audio_cache_key = (
                                    f"audio_duration_"
                                    f"{scene_id}"
                                )

                                if (
                                    audio_cache_key
                                    in st.session_state
                                ):

                                    del st.session_state[
                                        audio_cache_key
                                    ]

                                # Reload the editor so the backend
                                # becomes the source of truth.
                                fresh_data = (
                                    get_editor_data(
                                        api_url,
                                        video_id,
                                    )
                                )

                                remaining_scenes = (
                                    get_editor_scenes(
                                        fresh_data
                                    )
                                )

                                remaining_scene_ids = [
                                    get_editor_scene_id(
                                        item
                                    )
                                    for item in remaining_scenes
                                ]

                                remaining_scene_ids = [
                                    int(value)
                                    for value in (
                                        remaining_scene_ids
                                    )
                                    if value is not None
                                ]

                                if not remaining_scene_ids:

                                    raise RuntimeError(
                                        "The backend returned "
                                        "no scenes after deletion."
                                    )

                                # Normalize scene order after
                                # deletion.
                                reorder_editor_scenes(
                                    api_url=api_url,
                                    video_id=video_id,
                                    scene_ids=(
                                        remaining_scene_ids
                                    ),
                                )

                                fresh_data = (
                                    get_editor_data(
                                        api_url,
                                        video_id,
                                    )
                                )

                                # Recalculate contiguous
                                # start/end positions.
                                fresh_data = (
                                    rebuild_editor_timeline(
                                        api_url,
                                        fresh_data,
                                    )
                                )

                                st.session_state.editor_data = (
                                    fresh_data
                                )

                                # A previously exported file no longer
                                # represents the current editor state.
                                st.session_state.export_result = (
                                    None
                                )

                            st.success(
                                f"{scene_title} deleted successfully."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                f"Could not delete "
                                f"{scene_title}: {exc}"
                            )

                    if delete_disabled:

                        st.caption(
                            "Keep at least one scene."
                        )


        # ====================================================
        # REFRESH / REBUILD
        # ====================================================

        st.divider()

        refresh_col, rebuild_col, info_col = (
            st.columns(
                [1.2, 1.5, 3]
            )
        )

        with refresh_col:

            if st.button(
                "Refresh editor",
                use_container_width=True,
            ):

                try:

                    st.session_state.editor_data = (
                        get_editor_data(
                            api_url,
                            int(
                                editor_video[
                                    "id"
                                ]
                            ),
                        )
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Could not refresh editor: "
                        f"{exc}"
                    )

        with rebuild_col:

            if st.button(
                "Rebuild timeline",
                use_container_width=True,
            ):

                try:

                    with st.spinner(
                        "Rebuilding timeline..."
                    ):

                        fresh_data = (
                            rebuild_editor_timeline(
                                api_url,
                                editor_data,
                            )
                        )

                        st.session_state.editor_data = (
                            fresh_data
                        )

                    st.success(
                        "Timeline rebuilt successfully."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Timeline rebuild failed: "
                        f"{exc}"
                    )

        with info_col:

            st.caption(
                "Timeline positions follow the current "
                "scene durations. Narration duration "
                "is always protected."
            )


        # ====================================================
        # EXPORT
        # ====================================================

        st.divider()

        st.markdown(
            "## 05  Export"
        )

        st.caption(
            "Render the edited timeline into one final MP4."
        )

        if st.button(
            "Export final edited video ↗",
            type="primary",
            use_container_width=True,
        ):

            try:

                with st.spinner(
                    "Rendering your final edited video..."
                ):

                    export_data = (
                        export_editor_video(
                            api_url,
                            int(
                                editor_video[
                                    "id"
                                ]
                            ),
                        )
                    )

                    st.session_state.export_result = (
                        export_data
                    )

                st.success(
                    "Final edited video exported successfully."
                )

            except Exception as exc:

                st.error(
                    f"Export failed: {exc}"
                )


# ============================================================
# FINAL EXPORTED VIDEO
# ============================================================

if st.session_state.export_result:

    export_data = (
        st.session_state.export_result
    )

    st.divider()

    st.markdown(
        "## 06  Final edited video"
    )

    exported_file_url = (
        export_data.get(
            "file_url"
        )
        or export_data.get(
            "video_url"
        )
        or export_data.get(
            "url"
        )
    )

    exported_file_url = make_absolute_url(
        api_url,
        exported_file_url,
    )

    if exported_file_url:

        with st.container(
            border=True
        ):

            st.markdown(
                "### 🎬 Your final video is ready"
            )

            st.video(
                exported_file_url
            )

            st.link_button(
                "Open final edited video ↗",
                exported_file_url,
                use_container_width=True,
            )

            st.caption(
                f"Export URL: "
                f"{exported_file_url}"
            )

    else:

        st.warning(
            "The export succeeded, but the backend "
            "did not return a video URL."
        )

        with st.expander(
            "Show export response"
        ):

            st.json(
                export_data
            )