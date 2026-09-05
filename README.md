# End-to-End AI Video Creation Platform

A microservices-based AI platform that automatically transforms PDF documents into fully edited, AI-generated videos. The system extracts factual context via a Retrieval-Augmented Generation (RAG) pipeline, uses an LLM-powered agent to plan a structured scene-by-scene script, and compiles the final video using AI image generation, Text-to-Speech (TTS), and FFmpeg rendering.

## System Architecture

The platform relies on four isolated services working together in a seamless pipeline:

* **Frontend UI (Streamlit - Port 8501):** An interactive video editor interface for uploading documents, reviewing AI-generated scenes, and exporting the final cut.
* **RAG Backend (FastAPI - Port 8000):** Handles PDF ingestion, chunking, and contextual knowledge retrieval to ground the video script in factual data.
* **Media & Editor Backend (FastAPI - Port 8001):** Manages image generation (via Hugging Face), audio synthesis, asset management, and final video rendering using FFmpeg.
* **Agentic Planner (FastAPI - Port 8002):** Utilizes Groq LLMs to digest RAG context and automatically generate a multi-scene storyboard and narration script.

## Tech Stack

* **Backend:** Python, FastAPI, SQLAlchemy
* **Frontend:** Streamlit
* **AI & Machine Learning:** Groq (LLM processing), Hugging Face (Image Generation), LangChain (RAG)
* **Media Processing:** FFmpeg

## Prerequisites

* Python 3.10+
* **FFmpeg:** Must be installed and added to the system PATH. 
  * Windows users can install via: `winget install ffmpeg`

## Installation & Setup

### 1. **Clone the repository:**

```bash
git clone [https://github.com/nishajbabu/ai-video-creation-platform.git](https://github.com/nishajbabu/ai-video-creation-platform.git)
cd ai-video-creation-platform

```

### 2. **Configure Environment Variables:**

Create a `.env` file in the `final` directory and the backend directories. Required keys include:

```env
BASE_URL=[http://127.0.0.1:8001](http://127.0.0.1:8001)
GROQ_API_KEY_1=your_groq_key
GROQ_MODEL=openai/gpt-oss-20b
HF_TOKEN=your_huggingface_token
IMAGE_PROVIDER=huggingface

```

### 3. **Start the Microservices:**

Open separate terminal windows and start each service:

*RAG Backend:*

```bash
cd rag_module_backend
uvicorn main:app --port 8000

```

*Agentic Planner:*

```bash
cd agentic-backend
uvicorn app.main:app --port 8002

```

*Media Engine:*

```bash
cd final
uvicorn app.main:app --port 8001

```

*Streamlit Frontend:*

```bash
cd final
streamlit run streamlit_app.py

```

## Usage

1. Open `http://localhost:8501` in your browser.
2. Upload a reference PDF document and enter a brief prompt for the video's objective.
3. Click **Generate Script with AI** to extract data and build the storyboard.
4. Click **Generate Project** to synthesize the voiceover and visuals.
5. Click **Export final edited video** to compile the MP4.
