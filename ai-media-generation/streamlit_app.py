import os
from typing import Any

import requests
import streamlit as st


st.set_page_config(
    page_title="Frameforge | AI Media Studio",
    page_icon="F",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;700;800&display=swap');
    :root { --ink: #172322; --muted: #71817c; --line: #d7e0da; --paper: #f4f6f1; --coral: #e7674b; --teal: #1d7168; }
    .stApp { color: var(--ink); background: var(--paper); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #e8eee7; border-right: 1px solid var(--line); }
    .block-container { max-width: 1220px; padding-top: 3.5rem; padding-bottom: 5rem; }
    h1, h2, h3 { font-family: Manrope, sans-serif; letter-spacing: -1px; }
    h1 { font-size: clamp(2.8rem, 6vw, 5.3rem) !important; line-height: .98 !important; }
    h1 em { color: var(--teal); font-family: Georgia, serif; font-weight: 400; }
    p, label, .stMarkdown { font-family: Manrope, sans-serif; }
    .eyebrow { color: var(--coral); font: 500 10px 'DM Mono', monospace; letter-spacing: 1.4px; text-transform: uppercase; }
    .lede { max-width: 480px; color: var(--muted); font-size: 1rem; line-height: 1.7; }
    .scene-card { margin: 1.2rem 0 1.8rem; padding: 1.2rem 1.35rem .8rem; border: 1px solid var(--line); background: rgba(255,254,249,.76); }
    .scene-card h3 { margin: 0 0 1rem; color: var(--teal); font-size: 1rem; }
    .result-card { height: 100%; padding: .8rem; border: 1px solid var(--line); background: #fffef9; }
    .result-card h3 { margin: .65rem 0; font-size: 1rem; }
    .result-card audio { width: 100%; }
    div.stButton > button[kind="primary"] { background: var(--coral); border: 0; color: white; }
    div.stButton > button[kind="primary"]:hover { background: var(--teal); color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)


def new_scene() -> dict[str, Any]:
    return {"narration": "", "visual_prompt": "", "voice": "Auto"}


def reset_scenes() -> None:
    st.session_state.scenes = [
        {
            "narration": "Solar energy comes from sunlight.",
            "visual_prompt": "Solar panels receiving morning sunlight on a modern rooftop.",
            "voice": "Female",
        }
    ]


if "scenes" not in st.session_state:
    reset_scenes()

with st.sidebar:
    st.markdown("## frameforge")
    st.caption("AI media studio")
    st.divider()
    api_url = st.text_input(
        "FastAPI base URL",
        value=os.getenv("MEDIA_API_URL", "http://127.0.0.1:8000"),
        help="The URL where app.main:app is running.",
    ).rstrip("/")
    st.markdown("### Workflow")
    st.markdown("1. Write your scenes\n2. Choose a voice direction\n3. Generate the first cut")
    if st.button("Reset scenes", use_container_width=True):
        reset_scenes()
        st.rerun()

st.markdown('<p class="eyebrow">AI media studio / 01</p>', unsafe_allow_html=True)
st.markdown("# Turn a script into<br><em>something you can see.</em>", unsafe_allow_html=True)
st.markdown('<p class="lede">Shape your scenes, choose the voice, and let the media engine build the first cut.</p>', unsafe_allow_html=True)
st.write("")

with st.form("project_setup"):
    st.markdown("## 01  Project setup")
    project_id = st.text_input("Project name", value="my-first-film")
    st.markdown("## 02  Scenes")

    scenes_to_remove = []
    for index, scene in enumerate(st.session_state.scenes):
        with st.container(border=True):
            top_left, top_right = st.columns([5, 1])
            with top_left:
                st.markdown(f"### Scene {index + 1:02d}")
            with top_right:
                if len(st.session_state.scenes) > 1 and st.form_submit_button(
                    "Remove", key=f"remove_{index}"
                ):
                    scenes_to_remove.append(index)
            scene["narration"] = st.text_area(
                "Narration",
                value=scene["narration"],
                placeholder="What should the audience hear?",
                key=f"narration_{index}",
            )
            scene["visual_prompt"] = st.text_area(
                "Visual direction",
                value=scene["visual_prompt"],
                placeholder="Describe the image and atmosphere...",
                key=f"visual_{index}",
            )
            scene["voice"] = st.radio(
                "Voice direction",
                ["Auto", "Female", "Male"],
                index=["Auto", "Female", "Male"].index(scene["voice"]),
                horizontal=True,
                key=f"voice_{index}",
            )

    submitted = st.form_submit_button("Generate project ↗", type="primary", use_container_width=True)

if scenes_to_remove:
    st.session_state.scenes = [
        scene for index, scene in enumerate(st.session_state.scenes) if index not in scenes_to_remove
    ]
    st.rerun()

if st.button("+ Add scene", use_container_width=False):
    st.session_state.scenes.append(new_scene())
    st.rerun()

if submitted:
    if not project_id.strip():
        st.error("Enter a project name before generating.")
    elif any(not scene["narration"].strip() or not scene["visual_prompt"].strip() for scene in st.session_state.scenes):
        st.error("Every scene needs narration and a visual direction.")
    else:
        request_scenes = [
            {
                "scene_id": index + 1,
                "narration": scene["narration"].strip(),
                "visual_prompt": scene["visual_prompt"].strip(),
                "voice": None if scene["voice"] == "Auto" else scene["voice"].lower(),
            }
            for index, scene in enumerate(st.session_state.scenes)
        ]
        with st.spinner("Generating audio, images, and video..."):
            try:
                response = requests.post(
                    f"{api_url}/api/v1/projects/generate",
                    json={"project_id": project_id.strip(), "scenes": request_scenes},
                    timeout=1800,
                )
                response.raise_for_status()
                st.session_state.result = response.json()
            except requests.RequestException as exc:
                st.error(f"Could not reach the media API: {exc}")
            except ValueError:
                st.error("The media API returned an invalid response.")

if "result" in st.session_state:
    result = st.session_state.result
    st.divider()
    st.markdown(f"## 03  Your generated scenes · `{result['project_id']}`")
    scenes = result.get("scenes", [])
    columns = st.columns(min(3, max(1, len(scenes))))
    for index, scene in enumerate(scenes):
        with columns[index % len(columns)]:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.image(scene["image_url"], caption=f"Scene {scene['scene_id']:02d}")
            st.markdown(f"### Scene {scene['scene_id']:02d}")
            st.audio(scene["audio_url"])
            st.link_button("Open video ↗", scene["video_url"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
