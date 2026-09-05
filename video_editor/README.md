# AI Video Editor

A backend Video Editor and Rendering module for an AI Video Creation Platform.

The system takes AI-generated images and audio, manages them as video scenes and assets, creates timelines, applies text overlays and transitions, and finally combines the scenes into one final MP4 video.

## My Contribution

My main contribution is the **Video Editor and Rendering part** of the project.

I implemented:

- Video, Scene, Asset and Timeline management
- Integration of AI-generated media into the Video Editor
- Local image-to-video generation using FFmpeg
- Scene ordering and timeline management
- Automatic timeline generation
- Text overlays
- Fade transitions
- Scene-level video processing
- Audio and video synchronization
- Final video composition
- Final MP4 export
- API testing and debugging

The AI-generated images and narration are provided by the AI media-generation module. My module integrates those outputs into the Video Editor and handles the editing and rendering workflow.

## Workflow

```text
AI Generated Images + Audio
            |
            v
       Video Editor
            |
            v
    Video + Scenes + Assets
            |
            v
         Timeline
            |
            v
   Text + Transitions
            |
            v
          FFmpeg
            |
            v
       Final MP4 Video
```

## Project Structure

```text
video_editor/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── providers/
│   │   │   ├── image/
│   │   │   ├── video/
│   │   │   └── tts/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── storage/
│   │
│   ├── .env.example
│   └── requirements.txt
│
├── .gitignore
└── README.md
```

## Configuration

Create a `.env` file inside the `backend` folder.

Add the following configuration:

```env
BASE_URL=http://127.0.0.1:8001

IMAGE_PROVIDER=huggingface
HF_TOKEN=YOUR_HUGGINGFACE_TOKEN

VIDEO_PROVIDER=local

TTS_PROVIDER=edge
```

Replace `YOUR_HUGGINGFACE_TOKEN` with your actual Hugging Face token.

Do not commit the `.env` file or API keys to GitHub.

## How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/Shamsu0802/video_editor.git
cd video_editor
```

### 2. Go to the Backend

```bash
cd backend
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

#### Windows CMD

```bash
venv\Scripts\activate
```

#### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file inside the `backend` folder.

Add:

```env
BASE_URL=http://127.0.0.1:8001

IMAGE_PROVIDER=huggingface
HF_TOKEN=YOUR_HUGGINGFACE_TOKEN

VIDEO_PROVIDER=local

TTS_PROVIDER=edge
```

Replace `YOUR_HUGGINGFACE_TOKEN` with your actual Hugging Face token.

Do not commit the `.env` file or API keys to GitHub.

### 7. Verify the Application

Run:

```bash
python -c "from app.main import app; print('APP IMPORTED SUCCESSFULLY')"
```

Expected output:

```text
APP IMPORTED SUCCESSFULLY
```

### 8. Start the Backend Server

Run:

```bash
uvicorn app.main:app --reload --port 8001
```

The backend will run at:

```text
http://127.0.0.1:8001
```

### 9. Open Swagger UI

Open the following URL in your browser:

```text
http://127.0.0.1:8001/docs
```

Swagger UI can be used to test the available APIs.

## Video Configuration

The project currently uses the local video provider:

```env
VIDEO_PROVIDER=local
```

The local video provider uses FFmpeg to create video clips from generated images and narration audio.

The local video workflow:

```text
Generated Image
       +
Narration Audio
       |
       v
Local Video Provider
       |
       v
     FFmpeg
       |
       v
Scene Video
```

## Video Editing and Rendering

The Video Editor processes each scene individually.

Each scene can contain:

- Image
- Audio
- Video
- Duration
- Text overlay
- Transition

The rendering workflow is:

```text
Scene 1
   |
   +-- Image
   +-- Audio
   +-- Text
   +-- Transition
   |
   v
Processed Scene 1

Scene 2
   |
   +-- Image
   +-- Audio
   +-- Text
   +-- Transition
   |
   v
Processed Scene 2

Scene 3
   |
   +-- Image
   +-- Audio
   +-- Text
   +-- Transition
   |
   v
Processed Scene 3

        |
        v
      FFmpeg
        |
        v
   Final MP4 Video
```

## Generated Media

Generated media is stored inside:

```text
backend/media/
├── images/
├── audio/
├── videos/
└── exports/
```

The final exported videos are stored in:

```text
backend/media/exports/
```

## Output

For a multi-scene project, the system combines the processed scenes into one final video.

```text
Scene 1
   +
Scene 2
   +
Scene 3
   |
   v
Final Video.mp4
```

The final video contains the processed scene visuals, narration audio, text overlays and configured transitions.

## Testing

The project was tested using FastAPI Swagger UI and direct API requests.

The following workflow was tested:

- AI-generated media integration
- Scene creation
- Asset creation
- Timeline generation
- Timeline editing
- Text overlays
- Fade transitions
- Local image-to-video generation
- Audio/video synchronization
- Scene rendering
- Final video export

## Stop the Server

To stop the backend server, press:

```text
CTRL + C
```

GitHub Repository:

https://github.com/Shamsu0802/video_editor
