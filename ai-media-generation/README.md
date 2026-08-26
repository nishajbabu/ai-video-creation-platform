# AI Media Generation Service

## 1. Project Overview

The AI Media Generation Service is a FastAPI-based backend module that converts scene information into complete media assets.

For each scene, the service can generate:

- Text-to-Speech (TTS) audio
- AI-generated image
- Video using the generated image and audio
- HTTP-accessible media URLs for the generated files

The service supports both English and Tamil narration and provides male and female voice selection.

---

## 2. Module Responsibility

This module is responsible for converting scene-level content into media assets.

### Input

The module receives:

- `project_id`
- `scene_id`
- `narration`
- `visual_prompt`
- `voice`

### Processing

The service performs:

1. Voice selection
2. Text-to-Speech generation
3. AI image generation
4. Video generation
5. Local media storage
6. Media URL generation

### Output

For every scene, the service returns:

- Audio path
- Image path
- Video path
- Audio URL
- Image URL
- Video URL

---

## 3. Overall Architecture

```text
                 Person 1 Backend
                       |
                       | Scene Data
                       v
              +----------------------+
              | AI Media Generation  |
              |       Service        |
              +----------------------+
                       |
             +---------+---------+
             |         |         |
             v         v         v
        Voice       Image      Video
       Selector   Generation  Generation
             |         |         |
             v         v         v
            TTS      PNG       MP4
             |         |         |
             +---------+---------+
                       |
                       v
                Local Storage
                       |
                       v
                  Media URLs
```

---

## 4. Integration With Person 1 Backend

Person 1's backend provides scene information that can be consumed by the media-generation system.

The documented media-input structure contains:

```json
{
  "video_id": "video-001",
  "project_id": "project-001",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "Solar energy comes from sunlight.",
      "visual_prompt": "Solar panels receiving sunlight on a modern rooftop.",
      "voice": null
    }
  ]
}
```

The media-generation service uses the scene-level fields:

```text
scene_id
narration
visual_prompt
voice
```

The current media-generation project API uses:

```text
project_id
scenes[]
```

as its request structure.

> Note: `video_id` is part of the documented upstream integration structure, while the current `/api/v1/projects/generate` endpoint in this module accepts `project_id` and `scenes[]`.

---

## 5. Project Generation API

### Endpoint

```text
POST /api/v1/projects/generate
```

This endpoint generates media for one or more scenes.

---

## 6. Input Format

Example:

```json
{
  "project_id": "project-001",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "A farmer is working in his field.",
      "visual_prompt": "A farmer working in a green agricultural field.",
      "voice": "male"
    }
  ]
}
```

---

## 7. Input Field Description

| Field | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |
| `scenes` | array | Yes | List of scenes to generate |
| `scene_id` | integer | Yes | Unique scene number |
| `narration` | string | Yes | Text used to generate speech |
| `visual_prompt` | string | Yes | Prompt used for image/video generation |
| `voice` | string/null | No | `male`, `female`, or `null` |

---

## 8. Voice Selection

The user can specify the desired voice gender.

### Male

```json
"voice": "male"
```

The system selects:

**Tamil**

```text
ta-IN-ValluvarNeural
```

**English**

```text
en-US-AndrewNeural
```

### Female

```json
"voice": "female"
```

The system selects:

**Tamil**

```text
ta-IN-PallaviNeural
```

**English**

```text
en-US-AvaNeural
```

### Voice Not Provided

If:

```json
"voice": null
```

the system uses the default male voice.

The language is detected automatically from the narration.

```text
Tamil + null
    ↓
Tamil male voice

English + null
    ↓
English male voice
```

---

## 9. Language Detection

The `VoiceSelector` detects the language from the narration.

Supported languages:

- Tamil
- English

Tamil characters are detected using the Tamil Unicode range.

English characters are detected using ASCII alphabetic characters.

The detected language is then combined with the requested gender to select the appropriate Edge TTS voice.

---

## 10. Media Generation Pipeline

For each scene:

```text
Scene Input
    |
    +--------------------+
    |                    |
    v                    v
Narration          Visual Prompt
    |                    |
    v                    v
Voice Selector      Image Provider
    |                    |
    v                    v
TTS Audio             PNG Image
    |                    |
    +---------+----------+
              |
              v
        Video Provider
              |
              v
          MP4 Video
              |
              v
         Local Storage
              |
              v
          Media URLs
```

---

## 11. Generated Media

For a project such as:

```text
project-001
```

the generated files follow this naming pattern:

```text
media/
├── audio/
│   └── project-001_scene_1.mp3
│
├── images/
│   └── project-001_scene_1.png
│
└── videos/
    └── project-001_scene_1.mp4
```

---

## 12. API Response

Example response:

```json
{
  "project_id": "project-001",
  "scenes": [
    {
      "scene_id": 1,
      "audio_path": "media/audio/project-001_scene_1.mp3",
      "image_path": "media/images/project-001_scene_1.png",
      "video_path": "media/videos/project-001_scene_1.mp4",
      "audio_url": "http://127.0.0.1:8000/media/audio/project-001_scene_1.mp3",
      "image_url": "http://127.0.0.1:8000/media/images/project-001_scene_1.png",
      "video_url": "http://127.0.0.1:8000/media/videos/project-001_scene_1.mp4"
    }
  ]
}
```

---

## 13. Available API Endpoints

### Health Check

```text
GET /health
```

Returns the health status of the service.

### Text-to-Speech

```text
/api/v1/tts
```

Used for text-to-speech operations.

### Voices

```text
/api/v1/voices
```

Used for voice-related operations.

### Image Generation

```text
/api/v1/images
```

Used for image-generation operations.

### Scene Generation

```text
POST /api/v1/scenes/generate
```

Generates media for an individual scene.

### Batch Scene Generation

```text
POST /api/v1/scenes/generate-batch
```

Generates media for multiple scenes.

### Project Generation

```text
POST /api/v1/projects/generate
```

Generates complete media for a project containing one or more scenes.

---

## 14. Media Access

Generated media is exposed through FastAPI static files.

The application mounts:

```text
/media
```

For example:

```text
http://127.0.0.1:8000/media/audio/project-001_scene_1.mp3
```

```text
http://127.0.0.1:8000/media/images/project-001_scene_1.png
```

```text
http://127.0.0.1:8000/media/videos/project-001_scene_1.mp4
```

---

## 15. Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- Pydantic Settings

### Text-to-Speech

- Edge TTS

### Image Generation

- Hugging Face image provider

### Video Generation

- Local FFmpeg-based video generation
- Other configurable video providers are available in the project

### Testing

- Pytest

### Media Processing

- FFmpeg
- imageio-ffmpeg

---

## 16. Project Structure

```text
ai-media-generation/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── images.py
│   │       ├── projects.py
│   │       ├── scenes.py
│   │       ├── tts.py
│   │       └── voices.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── providers/
│   │   ├── factory.py
│   │   ├── image/
│   │   │   ├── existing_image_provider.py
│   │   │   ├── huggingface_provider.py
│   │   │   └── provider.py
│   │   │
│   │   ├── tts/
│   │   │   ├── edge_tts_provider.py
│   │   │   ├── edge_tts_voice_provider.py
│   │   │   ├── elevenlabls_provider.py
│   │   │   ├── provider.py
│   │   │   └── voice_provider.py
│   │   │
│   │   └── video/
│   │       ├── local_video_provider.py
│   │       ├── ltx_video_provider.py
│   │       ├── provider.py
│   │       └── runway_video_provider.py
│   │
│   ├── schemas/
│   │   ├── image.py
│   │   ├── project.py
│   │   ├── scene.py
│   │   ├── tts.py
│   │   └── voice.py
│   │
│   ├── services/
│   │   ├── image_service.py
│   │   ├── media_generation_service.py
│   │   ├── project_service.py
│   │   ├── scene_builder.py
│   │   ├── scene_service.py
│   │   ├── scene_splitter.py
│   │   ├── script_loader.py
│   │   ├── tts_service.py
│   │   ├── video_composition_service.py
│   │   ├── visual_prompt_generator.py
│   │   ├── voice_selector.py
│   │   └── voice_service.py
│   │
│   └── storage/
│       ├── local_storage.py
│       └── media_storage.py
│
├── media/
│   ├── audio/
│   ├── images/
│   └── videos/
│
├── tests/
│   ├── test_image.py
│   ├── test_storage.py
│   ├── test_tts.py
│   ├── test_video.py
│   └── test_voice_selector.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── AI_Media_Generation_Documentation.pdf
```

---

## 17. Installation

Move into the project directory:

```powershell
cd ai-media-generation
```

Create a virtual environment:

```powershell
python -m venv venv
```

Activate the virtual environment:

```powershell
.env\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

## 18. Environment Configuration

Create a `.env` file based on:

```text
.env.example
```

Provider API keys and configuration values should be stored in environment variables rather than hard-coded in the source code.

Do not commit secret API keys to GitHub.

---

## 19. Run the Application

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload
```

The application will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 20. Example API Request

PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/projects/generate" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "project_id": "project-001",
    "scenes": [
      {
        "scene_id": 1,
        "narration": "A farmer is working in his field.",
        "visual_prompt": "A farmer working in a green agricultural field.",
        "voice": "male"
      }
    ]
  }'
```

---

## 21. Multiple Scene Example

```json
{
  "project_id": "project-001",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "A farmer is preparing his field.",
      "visual_prompt": "A farmer preparing a green agricultural field.",
      "voice": "male"
    },
    {
      "scene_id": 2,
      "narration": "The farmer plants healthy seeds.",
      "visual_prompt": "A farmer planting seeds in fertile soil.",
      "voice": "female"
    },
    {
      "scene_id": 3,
      "narration": "The crops grow under bright sunlight.",
      "visual_prompt": "Healthy green crops growing under bright sunlight.",
      "voice": null
    }
  ]
}
```

---

## 22. Testing

The project uses Pytest for automated testing.

Run the complete test suite:

```powershell
python -m pytest -v
```

Current verified test result:

```text
27 passed
```

The test suite covers:

- Image generation
- Empty image prompts
- Image provider failures
- Audio generation
- Empty narration
- Empty voice IDs
- Storage validation
- Video generation
- Missing image handling
- Missing audio handling
- Voice selection
- Tamil voice selection
- English voice selection
- Male voice selection
- Female voice selection
- Default voice behavior
- Invalid voice handling

---

## 23. Voice Selector Tests

The voice selector is tested for:

```text
Tamil + male
→ ta-IN-ValluvarNeural
```

```text
Tamil + female
→ ta-IN-PallaviNeural
```

```text
English + male
→ en-US-AndrewNeural
```

```text
English + female
→ en-US-AvaNeural
```

When the voice is null:

```text
null
→ default male voice
```

---

## 24. Error Handling

The service validates incoming data and raises errors for invalid input.

Examples include:

- Empty narration
- Empty visual prompt
- Invalid voice
- Missing image
- Missing audio
- Invalid media filename
- Failed provider operation
- Failed FFmpeg operation
- Empty generated media

The API converts expected application errors into appropriate HTTP responses.

---

## 25. Media Storage

Generated files are stored locally under:

```text
media/
```

with separate directories for:

```text
media/audio/
media/images/
media/videos/
```

The local storage service ensures that media files are saved with valid filenames and verifies generated content.

---

## 26. Video Generation

The local video provider uses FFmpeg to create a video from the generated image.

When audio is available:

```text
Image
  +
Audio
  ↓
FFmpeg
  ↓
MP4 Video
```

The video uses the audio duration to determine the video duration.

The generated video is encoded using H.264 video and AAC audio.

---

## 27. Complete End-to-End Workflow

```text
1. Receive project and scene information
              ↓
2. Validate scene data
              ↓
3. Detect narration language
              ↓
4. Select male/female voice
              ↓
5. Generate TTS audio
              ↓
6. Generate image from visual prompt
              ↓
7. Generate video using image + audio
              ↓
8. Save audio/image/video
              ↓
9. Generate media URLs
              ↓
10. Return project response
```

---

## 28. Example End-to-End Result

Input:

```json
{
  "project_id": "project-001",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "A farmer is working in his field.",
      "visual_prompt": "A farmer working in a green agricultural field.",
      "voice": "male"
    }
  ]
}
```

Generated assets:

```text
media/audio/project-001_scene_1.mp3
media/images/project-001_scene_1.png
media/videos/project-001_scene_1.mp4
```

These assets were successfully generated during integration testing.

---

## 29. Design Principles

The module follows a provider/service architecture.

### Providers

Providers handle external or implementation-specific media generation.

Examples:

- Image Provider
- TTS Provider
- Video Provider

### Services

Services coordinate business logic.

Examples:

- `SceneService`
- `ProjectService`
- `VoiceSelector`
- `ImageService`
- `TTSService`

### Schemas

Pydantic schemas validate API input and output.

### Storage

The storage layer handles saving generated media files.

This separation makes providers replaceable without changing the main business logic.

---

## 30. Current Status

The AI Media Generation Service is currently functional for the implemented workflow.

Verified capabilities:

```text
✓ FastAPI application
✓ Project generation API
✓ Scene generation
✓ Multi-scene request support
✓ English narration
✓ Tamil narration
✓ Male voice
✓ Female voice
✓ Default voice when voice is null
✓ TTS generation
✓ AI image generation
✓ Video generation
✓ Local media storage
✓ Media URLs
✓ Automated testing
✓ Person 1 integration structure tested
```

Automated test status:

```text
27 passed
```

---

## 31. Future Improvements

Possible future improvements include:

- Cloud media storage
- Database-backed project management
- Asynchronous media generation
- Background job processing
- Progress tracking
- Better language detection
- More supported languages
- More TTS voice providers
- More image providers
- More video providers
- Video composition for multiple scenes
- Authentication and authorization
- Production deployment
- Docker support
- Cloud deployment

---

## 32. Summary

The AI Media Generation Service converts structured scene information into complete multimedia content.

The main pipeline is:

```text
Narration
   ↓
Voice Selection
   ↓
TTS Audio
   +
Visual Prompt
   ↓
AI Image
   +
Image + Audio
   ↓
Video
   ↓
Stored Media
   ↓
Media URLs
```

The service is designed to integrate with the upstream Agentic Backend and provide generated media assets to downstream components.

---

## Project Status

**AI Media Generation Module — Working**

**Automated Tests: 27 passed**
