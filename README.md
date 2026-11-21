# 🎙️ AI-Powered Multimodal Interview and Personality Assessment System

An intelligent, real-time multimodal candidate assessment platform that combines **Computer Vision**, **Acoustic & Speech Analysis**, and **Semantic NLP** to evaluate interview candidates comprehensively. The system aggregates signals across modalities using a weighted fusion engine to generate objective performance scores, behavioral insights, and targeted feedback.

---

## 👥 Project Information

### Team Members
- **Yashica G**
- **Balaji S**
- **Nidhi Mishra**
- **Gagan K**

### Faculty Guide
**Mr. Saurav Kumar Topo**  
*Department of Computer Science and Engineering*  
*CMR Institute of Technology (Affiliated to VTU)*

---

## 📌 Key Capabilities & Architecture

```
                               ┌─────────────────────────────────────────┐
                               │       Streamlit Frontend & Auth         │
                               └────────────────────┬────────────────────┘
                                                    │
                 ┌──────────────────────────────────┼──────────────────────────────────┐
                 │                                  │                                  │
                 ▼                                  ▼                                  ▼
     ┌───────────────────────┐          ┌───────────────────────┐          ┌───────────────────────┐
     │  Computer Vision (CV) │          │  Audio & Acoustics    │          │     Semantic NLP      │
     ├───────────────────────┤          ├───────────────────────┤          ├───────────────────────┤
     │ • MediaPipe (468 pts) │          │ • OpenAI Whisper STT  │          │ • Domain Question Bank│
     │ • Facial Emotion (FER)│          │ • Speaking Tempo (WPM)│          │ • Concept Extraction  │
     │ • Eye Contact & Gaze  │          │ • Filler Words (um/uh)│          │ • Sentence Transformer│
     │ • Head Pose Tracking  │          │ • Sound Classifier    │          │ • Cosine Similarity   │
     └───────────┬───────────┘          └───────────┬───────────┘          └───────────┬───────────┘
                 │                                  │                                  │
                 └──────────────────────────────────┼──────────────────────────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │    Multimodal Fusion Engine   │
                                    ├───────────────────────────────┤
                                    │ • Confidence Score            │
                                    │ • Communication Score         │
                                    │ • Emotional Stability Score   │
                                    │ • Interview Readiness Score   │
                                    │ • Overall Composite (0–100)   │
                                    └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │  Evaluation Report & Feedback │
                                    └───────────────────────────────┘
```

### 1. 👁️ Computer Vision Analysis
- **Face Landmark Mesh**: Uses MediaPipe FaceMesh to track 468 landmark points in real-time.
- **Eye Contact & Gaze Tracking**: Measures candidate gaze alignment and attention consistency with the camera.
- **Head Pose Estimation**: Analyzes pitch, yaw, and roll to detect posture and engagement.
- **Facial Emotion Recognition (FER)**: Deep learning CNN classifier detecting valence, expression shifts, and composure.

### 2. 🎙️ Acoustic & Speech Analysis
- **Speech-to-Text (STT)**: High-accuracy transcription using OpenAI Whisper.
- **Speech Metrics**: Evaluates speaking tempo (Words Per Minute), hesitation, pause distributions, and cadence.
- **Disfluency Detection**: Identifies filler words (*um*, *uh*, *like*, *you know*) to assess clarity.
- **Acoustic Profiling**: Analyzes ambient audio and background noise levels.

### 3. 🧠 Semantic NLP & Knowledge Matching
- **Role-Based Question Bank**: Curated technical and behavioral questions across Software Engineering, AI Engineering, Machine Learning, Data Analytics, and HR.
- **Concept Embeddings**: Uses Dense Vector Embeddings (Sentence Transformers) to match candidate answers against core domain concepts.
- **Knowledge Scoring**: Evaluates content depth and relevance using cosine similarity.

### 4. 📊 Multimodal Fusion & Scoring Engine
Combines normalized vision, acoustic, and NLP metrics into 4 core performance pillars:
- **Confidence Score**: Gaze consistency, head stability, and vocal steadiness.
- **Communication Score**: Pacing (WPM), articulation, and low filler-word frequency.
- **Emotional Stability Score**: Composure, neutral/positive facial valence, and emotional consistency.
- **Interview Readiness Score**: Content accuracy, technical concept coverage, and overall poise.
- **Performance Tiers**:
  - 🟢 **Exceptional Fit** (Score $\ge 85$)
  - 🟣 **Strong Candidate** ($70 \le \text{Score} < 85$)
  - 🟡 **Competent / Potential** ($50 \le \text{Score} < 70$)
  - 🔴 **Needs Development** ($\text{Score} < 50$)
- **Actionable Recommendations**: AI-generated improvement advice based on candidate weak spots.

---

## 🔐 Authentication, Profile & Security

- **Firebase Authentication**: Integrated using the Google Identity Toolkit REST API.
- **Email Verification**: Enforced on registration and sign-in; unverified accounts receive verification links before access is granted.
- **Self-Service Password Reset**: "Forgot password?" recovery dispatches password reset links.
- **Candidate Lobby & Dynamic Profile**: Automatically greets authenticated candidates with their name, email, and customizable square profile photo.
- **Square Profile Photo Management**:
  - Upload avatar (`PNG`, `JPG`, `JPEG`).
  - Interactive **Zoom/Scale** and **Alignment (Vertical & Horizontal)** sliders to frame face perfectly into an exact 1:1 square.
  - One-click **Remove Profile Photo** to reset to the default initial monogram.
- **Multi-Factor Authentication (MFA / 2FA)**:
  - Account security section supporting TOTP authenticator apps (**Google Authenticator**, **Microsoft Authenticator**, **Authy**).
  - Secret key and interactive QR code configuration with 6-digit verification code.
- **In-App Password Management**: Direct password updates and reset email triggers.
- **Secure Session Management**: Complete session teardown on logout.

---

## 🛠️ Tech Stack

| Domain | Technologies & Libraries |
|---|---|
| **Frontend & UI** | Streamlit, Custom Glassmorphism CSS, KaTeX |
| **Authentication & Cloud** | Firebase Identity Toolkit REST API, Python `requests` |
| **Computer Vision** | OpenCV, MediaPipe, Pillow (PIL), CVZone |
| **Deep Learning** | TensorFlow / Keras, PyTorch (CPU-optimized for deployment) |
| **Speech & Audio** | OpenAI Whisper, Librosa, SoundDevice, SciPy |
| **Natural Language Processing** | Sentence Transformers, Hugging Face Hub, Scikit-Learn |
| **Data & Math** | NumPy, Matplotlib |

---

## 📁 Repository Structure

```
AI-multimodal-assessment-system/
├── .devcontainer/             # Dev container configuration
├── .streamlit/
│   ├── config.toml            # Streamlit theme & server configuration
│   └── secrets.toml           # Firebase Web API key & secrets (Git-ignored)
├── backend/
│   ├── ai/
│   │   ├── answer_evaluator.py# Semantic concept matching & NLP scoring
│   │   └── question_bank.py   # Role-based interview question bank
│   ├── analytics/
│   │   └── timeline.py        # Interview telemetry timeline
│   ├── audio/
│   │   ├── audio_pipeline.py  # Audio capture & processing pipeline
│   │   ├── record_audio.py    # Microphone recording module
│   │   ├── sound_classifier.py# Background sound classifier
│   │   ├── speech_analyzer.py # WPM, cadence & filler-word analysis
│   │   └── speech_to_text.py  # Whisper STT wrapper
│   ├── models/
│   │   └── best_model.keras   # Trained facial emotion classification model
│   ├── scoring/
│   │   └── scoring_engine.py  # Multimodal fusion scoring & recommendations
│   ├── services/
│   │   └── interview_service.py # Orchestrator for camera, audio & AI analysis
│   ├── training/              # Model training scripts & datasets
│   ├── vision/
│   │   ├── emotion_detector.py# FER prediction using CNN
│   │   ├── eye_contact.py     # Gaze & eye contact ratio computation
│   │   ├── eye_tracker.py     # Iris & pupil tracking
│   │   ├── face_detector.py   # MediaPipe face bounding & detection
│   │   ├── head_pose.py       # 3D head pose estimation (pitch, yaw, roll)
│   │   └── vision_pipeline.py # Real-time frame processing loop
│   └── workers/
│       └── speech_nlp_worker.py# Isolated subprocess worker for Whisper & SentenceTransformers
├── frontend/
│   ├── app.py                 # Main Streamlit interview application & pages
│   ├── avatars/               # Saved candidate square profile photos (Git-ignored)
│   ├── auth/
│   │   ├── auth_ui.py         # Login, registration, MFA & settings UI
│   │   ├── firebase_auth.py   # Firebase Identity Toolkit REST API client
│   │   └── style.css          # Dark glassmorphism auth styles
│   └── components/
│       └── video_recorder/    # Browser-native WebRTC/HTML5 live camera & 16kHz audio recorder
├── docs/                      # Project documentation & review notes
├── Dockerfile                 # Production Linux Docker container definition
├── docker-compose.yml         # Multi-service container orchestration
├── .dockerignore              # Docker build exclusions
├── requirements.txt           # Python dependencies (CPU-optimized PyTorch & TensorFlow)
├── streamlit_app.py           # Entrypoint wrapper for cloud deployment
└── README.md                  # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10 – 3.12** installed on your system.
- A working **Webcam** and **Microphone**.
- A **Firebase Project** with **Email/Password** authentication enabled in the Firebase Console.

### 2. Clone the Repository
```bash
git clone https://github.com/balajis22/AI-multimodal-assessment-system.git
cd AI-multimodal-assessment-system
```

### 3. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip setuptools
pip install -r requirements.txt
```

### 5. Configure Firebase Credentials
Create a `.streamlit/secrets.toml` file in the project directory:

```toml
[firebase]
api_key = "YOUR_FIREBASE_WEB_API_KEY"
```

> **Note**: Alternatively, you can specify `firebase_api = YOUR_FIREBASE_WEB_API_KEY` in a root `.env` file. Both `.streamlit/secrets.toml` and `.env` are automatically ignored by Git to keep credentials secure.

### 6. Run the Application Locally
```bash
streamlit run streamlit_app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 🐳 Running with Docker

You can run the entire system inside a container without installing local Python packages:

### 1. Build and Run with Docker Compose (Recommended)
Make sure Docker Desktop is running, then run:
```bash
docker compose up --build
```
Navigate to `http://localhost:8501`.

### 2. Build and Run with Docker CLI
```bash
# Build the image
docker build -t ai-assessment-app .

# Run the container
docker run -p 8501:8501 --env-file .env ai-assessment-app
```

### 3. Run Backend CLI Evaluator in Container (Optional)
To run backend tasks or the standalone CLI script inside Docker:
```bash
docker compose run --rm backend-cli
# Or using Docker CLI:
docker run -it --rm ai-assessment-app python -m backend.app
```

---

## ☁️ Cloud & Production Deployment

### 1. 🚀 Render (Docker Web Service Deployment)

[Render](https://render.com) provides production-grade Docker container hosting with automated CI/CD builds, managed SSL certificates (HTTPS), and zero server maintenance. 

Because web browsers require **HTTPS** to allow webcam and microphone access, deploying this application on Render ensures full camera and audio recording functionality out of the box.

#### Step-by-Step Render Deployment:
1. **Push your code to GitHub**:
   Ensure all latest commits are pushed to your remote repository:
   ```bash
   git push origin main
   ```
2. **Create a New Web Service on Render**:
   - Log into your [Render Dashboard](https://dashboard.render.com).
   - Click **New +** in the top right corner and select **Web Service**.
   - Under **Connect a repository**, link your GitHub account and select `AI-multimodal-assessment-system` (or enter its Git repository URL).
3. **Configure Service Settings**:
   - **Name**: `ai-multimodal-assessment-system` (or your chosen service name).
   - **Region**: Select the region closest to your users (e.g., *Singapore*, *Frankfurt*, *Oregon*).
   - **Branch**: `main`.
   - **Runtime**: Select **Docker** (Render will automatically detect the root `Dockerfile`).
   - **Instance Type / Plan**: Select **Starter** or **Standard** (at least 1 GB – 2 GB RAM recommended to comfortably run Whisper and the facial emotion classification models in memory).
4. **Configure Environment Variables**:
   Click on the **Environment** tab and add the following key-value pairs:
   | Key | Value | Description |
   |---|---|---|
   | `FIREBASE_API_KEY` | `YOUR_FIREBASE_WEB_API_KEY` | Firebase Web API key for authentication |
   | `PORT` | `8501` | *Optional* (Render automatically binds dynamic `$PORT` via the Dockerfile) |
   | `PYTHONUNBUFFERED` | `1` | Ensures real-time console log streaming |
5. **Configure Health Check**:
   Under **Advanced Settings**, set the **Health Check Path** to:
   ```text
   /_stcore/health
   ```
6. **Deploy**:
   - Click **Create Web Service**.
   - Render will pull your repository, build the Docker container using `python:3.10-slim`, install system multimedia libraries (`ffmpeg`, `libportaudio2`, `libgl1`), download dependencies, and start Streamlit.
   - Once deployed, your app will be live at: `https://<your-service-name>.onrender.com`.

---

### 2. 🎈 Streamlit Community Cloud (Alternative Free Hosting)
This repository also includes a root `streamlit_app.py` entrypoint configured for direct deployment on Streamlit Community Cloud:

1. Push your repository to **GitHub**.
2. Connect your repository on [share.streamlit.io](https://share.streamlit.io/).
3. Set the **Main file path** to: `streamlit_app.py`.
4. In your Streamlit Cloud app settings, navigate to **Secrets** and add:
   ```toml
   [firebase]
   api_key = "YOUR_FIREBASE_WEB_API_KEY"
   ```
5. Deploy! Dependencies use CPU-optimized PyTorch and lazy-loaded singletons so the app stays lightweight and avoids unnecessary CUDA downloads.

---

### 3. 🌐 Cloud Architecture: Live Video & Audio Recording

Cloud container environments (Render Docker containers, Streamlit Cloud Linux instances) run in headless virtual machines without physical hardware webcams (`/dev/video0`) or physical audio cards (`sounddevice -1`).

To ensure seamless candidate interviews in cloud environments, this project uses a **Browser-Native Virtual Interview Architecture**:
- **Live Video Viewport (`frontend/components/video_recorder`)**: Uses HTML5 `getUserMedia` and `MediaStream` to stream the candidate's actual local webcam directly in the browser with 0ms latency.
- **Synchronized Audio & Video Recording**:
  - The browser's native `MediaRecorder` records the candidate's video response into a WebM stream.
  - An in-browser `AudioContext` simultaneously captures and resamples the candidate's voice into clean **16kHz mono PCM WAV** audio.
- **Process Isolation (Zero LLVM Conflicts)**:
  - Computer Vision analysis (MediaPipe FaceMesh + OpenCV + Emotion CNN) runs in the main application process.
  - Whisper speech transcription and SentenceTransformers semantic NLP run in an isolated worker subprocess (`backend/workers/speech_nlp_worker.py`).
  - This eliminates memory collisions between PyTorch and TensorFlow LLVM compilers on Linux servers.

---

## 📝 License & Academic Attribution
Developed as part of the Major Project curriculum for the Bachelor of Engineering program at **CMR Institute of Technology**, affiliated with **Visvesvaraya Technological University (VTU)**.
