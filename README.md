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
│   └── vision/
│       ├── emotion_detector.py# FER prediction using CNN
│       ├── eye_contact.py     # Gaze & eye contact ratio computation
│       ├── eye_tracker.py     # Iris & pupil tracking
│       ├── face_detector.py   # MediaPipe face bounding & detection
│       ├── head_pose.py       # 3D head pose estimation (pitch, yaw, roll)
│       └── vision_pipeline.py # Real-time frame processing loop
├── frontend/
│   ├── app.py                 # Main Streamlit interview application & pages
│   ├── avatars/               # Saved candidate square profile photos (Git-ignored)
│   └── auth/
│       ├── auth_ui.py         # Login, registration, MFA & settings UI
│       ├── firebase_auth.py   # Firebase Identity Toolkit REST API client
│       └── style.css          # Dark glassmorphism auth styles
├── docs/                      # Project documentation & review notes
├── requirements.txt           # Python dependencies
├── streamlit_app.py           # Entrypoint wrapper for Streamlit Cloud
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

## ☁️ Cloud Deployment

### 1. Streamlit Community Cloud (Recommended & Free)
This repository includes a root `streamlit_app.py` entrypoint configured for Streamlit Community Cloud:

1. Push your repository to **GitHub**.
2. Connect your repository on [share.streamlit.io](https://share.streamlit.io/).
3. Set the main file path to: `streamlit_app.py`.
4. In your Streamlit Cloud app settings, navigate to **Secrets** and add:
   ```toml
   [firebase]
   api_key = "YOUR_FIREBASE_WEB_API_KEY"
   ```
5. Deploy! Dependencies use CPU-only PyTorch so cloud deployments stay lightweight and fast without downloading CUDA packages.

### 2. Render (Docker Web Service)
1. In Render Dashboard, click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Select **Docker** as the runtime.
4. Under **Environment Variables**, add:
   - `FIREBASE_API_KEY`: `your_firebase_web_api_key`
5. Click **Create Web Service**. Render will automatically detect the `Dockerfile` and dynamic port `$PORT`.

---

## 📝 License & Academic Attribution
Developed as part of the Major Project curriculum for the Bachelor of Engineering program at **CMR Institute of Technology**, affiliated with **Visvesvaraya Technological University (VTU)**.
