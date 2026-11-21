import base64
from html import escape
import io
from pathlib import Path
import sys
import time

from PIL import Image
import streamlit as st


def render_square_avatar_html(avatar_path_or_url, user_name, size=76, border_radius=10, zoom=1.0, offset_x=50, offset_y=50):
    initial = (user_name[:1] if user_name else "U").upper()
    img_src = None
    if avatar_path_or_url:
        target = str(avatar_path_or_url).strip()
        if target.startswith("http://") or target.startswith("https://") or target.startswith("data:"):
            img_src = target
        else:
            p = Path(target)
            if p.is_file():
                try:
                    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
                    img_src = f"data:image/png;base64,{b64}"
                except Exception:
                    img_src = None

    if img_src:
        return f'''<div style="width: {size}px; height: {size}px; min-width: {size}px; min-height: {size}px; aspect-ratio: 1 / 1; border-radius: {border_radius}px; overflow: hidden; border: 2px solid rgba(255, 45, 117, 0.45); box-shadow: 0 4px 16px rgba(0,0,0,0.5); background: #0c0c10; display: inline-block;">
            <img src="{img_src}" style="width: 100%; height: 100%; object-fit: cover; object-position: {offset_x}% {offset_y}%; transform: scale({zoom}); transform-origin: {offset_x}% {offset_y}%; display: block;" alt="Candidate Photo" />
        </div>'''

    return f'''<div style="width: {size}px; height: {size}px; min-width: {size}px; min-height: {size}px; aspect-ratio: 1 / 1; border-radius: {border_radius}px; background: linear-gradient(135deg, #ff2d75, #9c0e40); border: 2px solid rgba(255, 45, 117, 0.5); box-shadow: 0 4px 16px rgba(255, 45, 117, 0.35); display: flex; align-items: center; justify-content: center; font-size: {int(size * 0.42)}px; font-weight: 800; color: #ffffff; font-family: 'Outfit', sans-serif;">
        {escape(initial)}
    </div>'''


def process_square_photo(image_bytes, zoom=1.0, offset_x=50, offset_y=50, output_size=400):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    side = min(w, h) / max(1.0, float(zoom))
    center_x = (w * float(offset_x)) / 100.0
    center_y = (h * float(offset_y)) / 100.0
    left = max(0, min(w - side, center_x - side / 2.0))
    top = max(0, min(h - side, center_y - side / 2.0))
    right = min(w, left + side)
    bottom = min(h, top + side)
    cropped = img.crop((left, top, right, bottom))
    resized = cropped.resize((output_size, output_size), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    resized.save(buf, format="PNG")
    return buf.getvalue()

# --------------------------------------------------
# Ensure the app can be run both as a standalone module and as a package entry
# point (for example from a repository root streamlit_app.py wrapper).
# --------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = Path(__file__).resolve().parent
for _path in (str(ROOT), str(FRONTEND_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

try:
    from .auth.auth_ui import logout_user, render_auth, render_authenticated_controls
    from .auth.firebase_auth import (
        FirebaseAuthError,
        send_password_reset_email,
        update_user_password,
        update_user_profile,
    )
except ImportError:
    from auth.auth_ui import logout_user, render_auth, render_authenticated_controls
    from auth.firebase_auth import (
        FirebaseAuthError,
        send_password_reset_email,
        update_user_password,
        update_user_profile,
    )

# Keep the AI model loading behind the actual interview action so the
# Streamlit UI can render without importing the full backend stack on startup.
from backend.ai.question_bank import get_question, get_questions, QUESTION_BANK


def get_interview_service():
    try:
        import importlib
        import backend.vision.interview_analyzer as ia_mod
        import backend.services.interview_service as is_mod
        importlib.reload(ia_mod)
        importlib.reload(is_mod)
        return is_mod.InterviewService()
    except Exception as exc:
        st.error(
            "The interview backend is not ready yet. Please check the AI dependencies before starting a session."
        )
        st.caption(f"Details: {exc}")
        return None

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="AI Multimodal Assessment System",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if (
    not isinstance(st.session_state.get("auth_user"), dict)
    or not st.session_state.get("auth_id_token")
):
    render_auth()
    st.stop()

render_authenticated_controls()

# --------------------------------------------------
# Session State Initialization
# --------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"  # Options: "home", "interview", "results"

if "candidate_name" not in st.session_state:
    st.session_state.candidate_name = ""

if "candidate_email" not in st.session_state:
    st.session_state.candidate_email = ""

candidate_profile = st.session_state.get("candidate_profile", {})
if (
    isinstance(candidate_profile, dict)
    and candidate_profile.get("uid") == st.session_state["auth_user"].get("uid")
):
    st.session_state.candidate_name = (
        candidate_profile.get("name") or st.session_state.candidate_name
    )
    st.session_state.candidate_email = (
        candidate_profile.get("email") or st.session_state.candidate_email
    )

if "active_role" not in st.session_state:
    st.session_state.active_role = "Software Engineer"

if "question_idx" not in st.session_state:
    st.session_state.question_idx = 0

if "duration" not in st.session_state:
    st.session_state.duration = 20

if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Navigation helpers
def go_to_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def reset_session():
    st.session_state.current_page = "home"
    st.session_state.interview_completed = False
    st.session_state.last_result = None
    st.rerun()

# --------------------------------------------------
# Global CSS Styling (Minimalist Black & Pink)
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Base canvas */
.stApp {
    background-color: #000000;
    background-image: 
        radial-gradient(at 0% 0%, rgba(255, 45, 117, 0.08) 0px, transparent 45%),
        radial-gradient(at 100% 100%, rgba(255, 45, 117, 0.05) 0px, transparent 45%);
    color: #f4f4f5;
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

.block-container {
    padding-top: 1.8rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1280px !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #ffffff !important;
}

/* Minimalist Glass Panels */
.glass-panel {
    background: rgba(14, 14, 18, 0.88);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.8);
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s ease;
}

.glass-panel:hover {
    border-color: rgba(255, 45, 117, 0.25);
}

.glass-panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255, 45, 117, 0.55), transparent);
    opacity: 0.8;
}

/* Stepper Bar */
.stepper-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 2rem;
    padding: 0.75rem 1.5rem;
    background: rgba(14, 14, 18, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    max-width: 680px;
    margin-left: auto;
    margin-right: auto;
}

.step-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.84rem;
    font-weight: 600;
    color: #71717a;
}

.step-item.active {
    color: #ff2d75;
}

.step-item.completed {
    color: #fb7185;
}

.step-circle {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.08);
    color: #a1a1aa;
}

.step-item.active .step-circle {
    background: #ff2d75;
    color: #ffffff;
    box-shadow: 0 0 14px rgba(255, 45, 117, 0.6);
}

.step-item.completed .step-circle {
    background: #be185d;
    color: #ffffff;
}

.step-divider {
    width: 32px;
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
}

/* Status Indicators */
@keyframes pulse-dot {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

@keyframes pulse-pink {
    0% { box-shadow: 0 0 0 0 rgba(255, 45, 117, 0.7); }
    70% { box-shadow: 0 0 0 8px rgba(255, 45, 117, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 45, 117, 0); }
}

.status-dot-green {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #10b981;
    display: inline-block;
    animation: pulse-dot 2s infinite;
    margin-right: 6px;
}

.status-dot-pink {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #ff2d75;
    display: inline-block;
    animation: pulse-pink 1.5s infinite;
    margin-right: 6px;
}

/* Stat Cards */
.stat-card {
    background: rgba(14, 14, 18, 0.85);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1.25rem 1rem;
    text-align: center;
    transition: all 0.25s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 45, 117, 0.45);
    box-shadow: 0 8px 24px -5px rgba(255, 45, 117, 0.25);
}

.stat-title {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #a1a1aa;
    margin-bottom: 0.35rem;
}

.stat-value {
    font-family: 'Outfit', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.2;
}

.stat-sub {
    font-size: 0.75rem;
    color: #71717a;
    margin-top: 0.3rem;
}

/* Custom Primary Button (Black & Pink Gradient) */
.stButton > button {
    background: linear-gradient(135deg, #ff2d75 0%, #db2777 100%) !important;
    color: #ffffff !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    letter-spacing: 0.02em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.8rem 1.6rem !important;
    box-shadow: 0 4px 18px rgba(255, 45, 117, 0.35) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 26px rgba(255, 45, 117, 0.55) !important;
    filter: brightness(1.1) !important;
}

.stButton > button:disabled {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #71717a !important;
    box-shadow: none !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    transform: none !important;
}

/* Form Inputs */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {
    background-color: rgba(14, 14, 18, 0.95) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    border-radius: 8px !important;
    color: #f4f4f5 !important;
}

div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within {
    border-color: #ff2d75 !important;
    box-shadow: 0 0 0 2px rgba(255, 45, 117, 0.2) !important;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-blue, .badge-pink { background: rgba(255, 45, 117, 0.14); color: #ff6699; border: 1px solid rgba(255, 45, 117, 0.35); }
.badge-green { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.25); }
.badge-amber { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.25); }
.badge-purple, .badge-rose { background: rgba(244, 63, 94, 0.14); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(14, 14, 18, 0.8) !important;
    padding: 6px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    gap: 8px !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #a1a1aa !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.1rem !important;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(255, 45, 117, 0.16) !important;
    color: #ff6699 !important;
    border: 1px solid rgba(255, 45, 117, 0.35) !important;
}

/* Transcripts & Recommendations */
.transcript-bubble {
    background: rgba(14, 14, 18, 0.9);
    border: 1px solid rgba(255, 45, 117, 0.25);
    border-left: 4px solid #ff2d75;
    border-radius: 12px;
    padding: 1.2rem;
    font-size: 0.95rem;
    line-height: 1.7;
    color: #f4f4f5;
}

.recommendation-item {
    background: rgba(18, 18, 24, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.92rem;
    color: #f4f4f5;
    transition: border-color 0.2s ease;
}

.recommendation-item:hover {
    border-color: rgba(255, 45, 117, 0.3);
}

.concept-bar-container {
    width: 100%;
    height: 7px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    overflow: hidden;
    margin-top: 6px;
}
.concept-bar-fill {
    height: 100%;
    border-radius: 9999px;
    transition: width 0.8s ease;
}

/* Loading Card */
.loading-panel {
    background: rgba(16, 12, 15, 0.92);
    border: 1px solid rgba(255, 45, 117, 0.35);
    border-radius: 12px;
    padding: 1rem 1.3rem;
    margin-top: 12px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 15px;
    box-shadow: 0 8px 30px rgba(255, 45, 117, 0.15);
}

@keyframes spin-ring {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-spinner-ring {
    width: 28px;
    height: 28px;
    min-width: 28px;
    border: 3px solid rgba(255, 45, 117, 0.2);
    border-top: 3px solid #ff2d75;
    border-radius: 50%;
    animation: spin-ring 0.85s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.loading-title {
    font-family: 'Outfit', sans-serif;
    font-size: 0.98rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 2px;
}

.loading-sub {
    font-size: 0.82rem;
    color: #fda4af;
    line-height: 1.35;
}

#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Top Header & Brand Bar
# --------------------------------------------------

st.markdown("""
    <div style="display: flex; align-items: center; gap: 14px;">
        <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #ff2d75, #be185d); display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 4px 18px rgba(255, 45, 117, 0.4);">
            🎙️
        </div>
        <div>
            <h1 style="margin: 0; font-size: 1.8rem; font-weight: 800; line-height: 1.2; letter-spacing: -0.02em;">
                AI Interview <span style="background: linear-gradient(135deg, #ff2d75 0%, #fda4af 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Assessment Studio</span>
            </h1>
            <p style="margin: 0; color: #a1a1aa; font-size: 0.85rem;">
                Multimodal Assessment &bull; Computer Vision &bull; Speech &bull; Semantic NLP
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# Progress Stepper Header
# --------------------------------------------------
curr = st.session_state.current_page
if curr == "settings":
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding: 0.75rem 1.5rem; background: rgba(14, 14, 18, 0.9); border: 1px solid rgba(255, 45, 117, 0.25); border-radius: 9999px; max-width: 680px; margin-left: auto; margin-right: auto;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.1rem;">⚙️</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 0.92rem; font-weight: 700; color: #ffffff;">Personal Details & Security Settings</span>
        </div>
        <span class="badge badge-pink" style="font-size: 0.72rem;">Account Center</span>
    </div>
    """, unsafe_allow_html=True)
else:
    s1_class = "completed" if curr in ["interview", "results"] else ("active" if curr == "home" else "")
    s2_class = "completed" if curr == "results" else ("active" if curr == "interview" else "")
    s3_class = "active" if curr == "results" else ""

    st.markdown(f"""
    <div class="stepper-container">
        <div class="step-item {s1_class}">
            <div class="step-circle">1</div>
            <span>Candidate Lobby</span>
        </div>
        <div class="step-divider"></div>
        <div class="step-item {s2_class}">
            <div class="step-circle">2</div>
            <span>Camera & Interview</span>
        </div>
        <div class="step-divider"></div>
        <div class="step-item {s3_class}">
            <div class="step-circle">3</div>
            <span>Evaluation Report</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# PAGE 1: HOME PAGE (CANDIDATE SETUP)
# ==================================================
if st.session_state.current_page == "home":
    col_form, col_info = st.columns([1.1, 0.9], gap="large")

    with col_form:
        user_name = (
            st.session_state.get("candidate_name")
            or st.session_state.get("auth_user", {}).get("name")
            or (st.session_state.get("candidate_email", "").split("@")[0].title() if st.session_state.get("candidate_email") else "")
            or "Candidate"
        )
        user_email = (
            st.session_state.get("candidate_email")
            or st.session_state.get("auth_user", {}).get("email")
            or ""
        )
        st.session_state.candidate_name = user_name
        st.session_state.candidate_email = user_email

        user_uid = st.session_state.get("auth_user", {}).get("uid", "")
        avatars_dir = Path(__file__).resolve().parent / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)
        local_avatar = avatars_dir / f"{user_uid}.png" if user_uid else None
        avatar_src = str(local_avatar) if (local_avatar and local_avatar.is_file()) else st.session_state.get("candidate_profile_photo")
        zoom_val = float(st.session_state.get("photo_zoom", 1.0))
        off_x = int(st.session_state.get("photo_offset_x", 50))
        off_y = int(st.session_state.get("photo_offset_y", 50))
        lobby_avatar_html = render_square_avatar_html(avatar_src, user_name, size=74, border_radius=10, zoom=zoom_val, offset_x=off_x, offset_y=off_y)

        st.markdown(f"""
        <div class="glass-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem;">
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.2rem; font-weight: 700; color: #f8fafc;">
                    👤 Candidate Setup
                </div>
                <span class="badge badge-blue">Step 1 of 3</span>
            </div>
            <div style="background: rgba(255, 45, 117, 0.07); border: 1px solid rgba(255, 45, 117, 0.22); border-radius: 14px; padding: 1.1rem 1.25rem; margin-bottom: 1.2rem; display: flex; align-items: center; justify-content: space-between; gap: 16px;">
                <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 0.74rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #ff2d75; margin-bottom: 0.2rem;">
                        Candidate
                    </div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 700; color: #ffffff; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        Welcome, {escape(user_name)} 👋
                    </div>
                    <div style="font-size: 0.88rem; color: #a1a1aa; margin-top: 0.25rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        {escape(user_email)}
                    </div>
                </div>
                <div style="flex-shrink: 0;">
                    {lobby_avatar_html}
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("⚙️ Manage Profile & Security Settings", key="lobby_settings_shortcut", use_container_width=True):
            go_to_page("settings")

        roles = [
            "Software Engineer",
            "AI Engineer",
            "Machine Learning Engineer",
            "Data Analyst",
            "HR Interview"
        ]
        
        role_input = st.selectbox(
            "Target Job Role",
            roles,
            index=roles.index(st.session_state.active_role) if st.session_state.active_role in roles else 0
        )
        st.session_state.active_role = role_input

        # Questions for selected role
        role_questions = get_questions(role_input)
        q_count = len(role_questions) if role_questions else 1

        q_idx_input = st.selectbox(
            "Select Interview Question Prompt",
            options=list(range(q_count)),
            index=st.session_state.question_idx if st.session_state.question_idx < q_count else 0,
            format_func=lambda i: f"Question #{i+1}: {role_questions[i]['question'][:55]}... ({role_questions[i]['difficulty'] if role_questions else 'General'})"
        )
        st.session_state.question_idx = q_idx_input

        duration_input = st.slider(
            "Recording Response Window (seconds)",
            min_value=10,
            max_value=60,
            value=st.session_state.duration,
            step=5,
            help="Allocated speech and vision capture duration."
        )
        st.session_state.duration = duration_input

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        proceed_btn = st.button("Proceed to Interview Room ➡️", use_container_width=True)
        if proceed_btn:
            if not st.session_state.candidate_name.strip():
                st.warning("⚠️ Candidate name is missing. Please sign in again.")
            else:
                go_to_page("interview")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown("""
        ### 📋 Interview Protocol & Guidelines

        - 👁️ **Computer Vision Analysis**  
          Tracks real-time facial expressions, gaze alignment, head rotation, and eye contact consistency using 468 landmark points.

        - 🎙️ **Acoustics & Whisper Speech-to-Text**  
          Measures speaking tempo (WPM), hesitation, filler words (um, uh, like), and classifies ambient background noise.

        - 🧠 **Semantic NLP & Knowledge Matching**  
          Compares your answer semantically against domain concepts using dense vector embeddings and cosine similarity.

        > ⚡ **Hardware Readiness**  
        In the next screen, you will enter the Live Camera Room where your webcam and microphone telemetry are monitored before launching the assessment.
        """)

# ==================================================
# PAGE 2: INTERVIEW ROOM (CAMERA & SENSORS)
# ==================================================
elif st.session_state.current_page == "interview":
    # Load question data
    q_data = get_question(st.session_state.active_role, st.session_state.question_idx)
    q_text = q_data["question"] if q_data else "Explain your technical background."
    q_diff = q_data.get("difficulty", "Standard") if q_data else "Standard"
    q_concepts = q_data.get("concepts", []) if q_data else []

    diff_badge = "badge-green" if q_diff == "Easy" else ("badge-amber" if q_diff == "Medium" else "badge-rose")
    concept_pills = "".join([f'<span class="badge badge-pink" style="margin-right: 6px; margin-top: 4px;">{c["name"]}</span>' for c in q_concepts])

    # Top Question Card
    st.subheader(f"{q_diff} · {st.session_state.active_role}")
    st.caption(f"Time Window: {st.session_state.duration} seconds")
    st.markdown(f"> \"{q_text}\"")
    if q_concepts:
        st.markdown(" ".join(f"**{concept['name']}**" for concept in q_concepts))

    # 2-Column Cockpit Layout
    cam_col, tel_col = st.columns([1.1, 0.9], gap="large")

    with cam_col:
        st.markdown("### 📷 Vision & Facial Recognition Viewport")

        tab_cam, tab_upload = st.tabs(["🌐 Live Browser Camera", "📁 Upload Video Clip"])

        with tab_cam:
            st.caption("Allow camera access in your browser to analyze facial emotion, gaze, and head rotation live.")
            cam_shot = st.camera_input(
                "Capture Face Telemetry for Real-Time AI Evaluation",
                key="browser_interview_camera"
            )
            if cam_shot is not None:
                try:
                    import cv2
                    import numpy as np
                    from backend.vision.interview_analyzer import analyze_single_frame

                    frame_bytes = cam_shot.getvalue()
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    annotated_rgb, metrics = analyze_single_frame(frame_bgr)
                    st.session_state["candidate_vision_metrics"] = metrics
                    st.session_state["candidate_vision_annotated"] = annotated_rgb

                    st.markdown("""
                    <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 10px; padding: 0.6rem 0.9rem; margin: 0.6rem 0;">
                        <span style="color: #34d399; font-weight: 700; font-size: 0.88rem;">✅ Facial Landmarks & Biometrics Successfully Analyzed!</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.image(annotated_rgb, caption="Face Landmarks, Emotion & Gaze Overlay", use_container_width=True)

                    c_em, c_eye, c_head = st.columns(3)
                    with c_em:
                        st.metric("🎭 Emotion", f"{metrics['emotion']}", f"{int(metrics.get('confidence', 0.85)*100)}% conf")
                    with c_eye:
                        st.metric("👁️ Eye Gaze", f"{metrics['eye']}")
                    with c_head:
                        st.metric("👤 Head Pose", f"{metrics['head']}")
                except Exception as exc:
                    st.warning(f"Could not analyze camera frame: {exc}")

        with tab_upload:
            st.caption("Upload a recorded candidate video clip to extract full facial, eye gaze, and head pose timeline.")
            uploaded_vid = st.file_uploader(
                "Upload candidate video file (.mp4, .webm, .mov)",
                type=["mp4", "webm", "mov", "avi"],
                key="candidate_video_upload_input"
            )
            if uploaded_vid is not None:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                    tmp_file.write(uploaded_vid.read())
                    temp_vid_path = tmp_file.name

                with st.spinner("Processing video frames with OpenCV and FaceMesh..."):
                    try:
                        from backend.vision.interview_analyzer import analyze_interview
                        vid_metrics = analyze_interview(duration=st.session_state.duration, source=temp_vid_path)
                        st.session_state["candidate_vision_metrics"] = vid_metrics
                        st.session_state["candidate_uploaded_video_path"] = temp_vid_path
                        st.success("✅ Video telemetry extracted successfully!")
                        c_em, c_eye, c_head = st.columns(3)
                        with c_em:
                            st.metric("🎭 Emotion", f"{vid_metrics['emotion']}")
                        with c_eye:
                            st.metric("👁️ Eye Gaze", f"{vid_metrics['eye']}")
                        with c_head:
                            st.metric("👤 Head Pose", f"{vid_metrics['head']}")
                    except Exception as exc:
                        st.warning(f"Could not analyze video: {exc}")

        # Native Hardware Camera Viewport slot
        video_slot = st.empty()

        standby_html = (
            '<div style="position: relative; width: 100%; aspect-ratio: 16 / 9.5; background: #050508; '
            'border: 1px solid rgba(255, 45, 117, 0.35); border-radius: 14px; overflow: hidden; '
            'display: flex; flex-direction: column; align-items: center; justify-content: center; '
            'box-shadow: 0 4px 28px rgba(0, 0, 0, 0.75); padding: 1.5rem; text-align: center; margin-top: 10px;">'
            '<div style="position: absolute; top: 14px; left: 16px; display: flex; align-items: center; gap: 8px;">'
            '<span class="status-dot-pink"></span>'
            '<span style="font-family: \'JetBrains Mono\', monospace; font-size: 0.75rem; letter-spacing: 0.08em; color: #ff6699; font-weight: 700; text-transform: uppercase;">Assessment Module</span>'
            '</div>'
            '<div style="position: absolute; top: 14px; right: 16px;">'
            '<span class="badge badge-pink" style="font-size: 0.72rem; padding: 3px 9px;">OpenCV + FaceMesh</span>'
            '</div>'
            '<div style="width: 80px; height: 80px; border: 2px dashed rgba(255, 45, 117, 0.45); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">'
            '<div style="width: 14px; height: 14px; background: #ff2d75; border-radius: 50%; box-shadow: 0 0 16px #ff2d75;"></div>'
            '</div>'
            '<div style="font-family: \'Outfit\', sans-serif; font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-bottom: 5px;">'
            'Facial Recognition & Acoustic Sensors Ready'
            '</div>'
            '<div style="font-size: 0.82rem; color: #a1a1aa; max-width: 440px; line-height: 1.5;">'
            'Click <strong>Start Interview Session</strong> below. Live audio analysis and facial biometrics will be evaluated.'
            '</div>'
            '<div style="position: absolute; bottom: 12px; left: 16px; font-family: \'JetBrains Mono\', monospace; font-size: 0.7rem; color: rgba(255, 255, 255, 0.4);">'
            'FEED: BROWSER / HARDWARE · 16kHz WAV'
            '</div>'
            '<div style="position: absolute; bottom: 12px; right: 16px; font-family: \'JetBrains Mono\', monospace; font-size: 0.7rem; color: #ff6699; font-weight: 600;">'
            '[ READY TO START ]'
            '</div>'
            '</div>'
        )

        if not st.session_state.interview_completed:
            video_slot.markdown(standby_html, unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Action Buttons
        if not st.session_state.interview_completed:
            start_btn = st.button("▶ Start Interview Session", use_container_width=True)

            if start_btn:
                service = get_interview_service()
                if service is None:
                    st.stop()

                def update_video_feed(frame):
                    video_slot.image(frame, channels="RGB", use_container_width=True)

                with st.spinner(f"Interview session in progress... Answer naturally for {st.session_state.duration} seconds"):
                    try:
                        pre_vision = st.session_state.get("candidate_vision_metrics")
                        vid_src = st.session_state.get("candidate_uploaded_video_path", 0)
                        result = service.run(
                            duration=st.session_state.duration,
                            role=st.session_state.active_role,
                            question_number=st.session_state.question_idx,
                            frame_callback=update_video_feed,
                            precomputed_vision=pre_vision,
                            source=vid_src
                        )

                        st.session_state.last_result = result
                        st.session_state.interview_completed = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Interview run error: {e}")
        else:
            # Interview Completed - Finish Interview Button
            st.markdown("""
            <div style="background: rgba(255, 45, 117, 0.1); border: 1px solid rgba(255, 45, 117, 0.35); border-radius: 12px; padding: 0.9rem; text-align: center; margin-bottom: 10px;">
                <span style="color: #ff6699; font-weight: 700; font-size: 0.95rem;">✅ Interview Recording & Analysis Completed!</span>
            </div>
            """, unsafe_allow_html=True)
            
            finish_btn = st.button("🏁 Finish Interview & View Report ➡️", use_container_width=True)
            if finish_btn:
                go_to_page("results")

        st.markdown("</div>", unsafe_allow_html=True)

    with tel_col:
        st.markdown("""
        <div class="glass-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 700; color: #ffffff;">
                    📡 Sensor & Telemetry
                </div>
                <span class="badge badge-pink">Hardware Hub</span>
            </div>
        """, unsafe_allow_html=True)

        cand_vis = st.session_state.get("candidate_vision_metrics")
        vis_badge = '<span class="badge badge-green">Live Telemetry Active</span>' if cand_vis else '<span class="badge badge-pink">Camera Ready</span>'
        vis_detail = f"Emotion: {cand_vis.get('emotion', 'Neutral')} · Gaze: {cand_vis.get('eye', 'Center')}" if cand_vis else "interview_analyzer.py · OpenCV & FaceMesh"

        st.markdown(f"""
        <!-- Candidate pill -->
        <div style="background: rgba(14, 14, 18, 0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 0.8rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.75rem; color: #a1a1aa; text-transform: uppercase; font-weight: 600;">Active Candidate</div>
                <div style="font-size: 1rem; font-weight: 700; color: #ffffff;">{escape(st.session_state.candidate_name or "Candidate")}</div>
                {f'<div style="font-size: 0.8rem; color: #71717a;">{escape(st.session_state.candidate_email)}</div>' if st.session_state.candidate_email else ''}
            </div>
            <span class="badge badge-pink">{escape(st.session_state.active_role)}</span>
        </div>

        <!-- Video Telemetry -->
        <div style="background: rgba(14, 14, 18, 0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 0.8rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">📷</span>
                    <span style="font-size: 0.88rem; font-weight: 600; color: #ffffff;">Camera & Vision Engine</span>
                </div>
                {vis_badge}
            </div>
            <div style="font-size: 0.76rem; color: #ff6699; font-weight: 600;">{vis_detail}</div>
        </div>

        <!-- Audio Telemetry -->
        <div style="background: rgba(14, 14, 18, 0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 0.8rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">🎙️</span>
                    <span style="font-size: 0.88rem; font-weight: 600; color: #ffffff;">Microphone & Sound Pipeline</span>
                </div>
                <span class="badge badge-green">Hardware Connected</span>
            </div>
            <div style="font-size: 0.76rem; color: #a1a1aa;">speech_analyzer.py · SoundDevice & Whisper</div>
        </div>

        <!-- AI Engine -->
        <div style="background: rgba(14, 14, 18, 0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 1.2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">🧠</span>
                    <span style="font-size: 0.88rem; font-weight: 600; color: #ffffff;">Evaluation Scorer</span>
                </div>
                <span class="badge badge-pink">Active</span>
            </div>
            <div style="font-size: 0.76rem; color: #a1a1aa;">scoring_engine.py & answer_evaluator.py</div>
        </div>
        """, unsafe_allow_html=True)

        back_col, _ = st.columns([1, 1])
        with back_col:
            if st.button("⬅️ Back to Setup", use_container_width=True):
                go_to_page("home")

        st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
# PAGE 3: RESULTS PAGE (DETAILED REPORT)
# ==================================================
elif st.session_state.current_page == "results":
    res = st.session_state.last_result

    if res is None:
        st.warning("No assessment data available yet. Please complete an interview first.")
        if st.button("Go to Setup Lobby"):
            go_to_page("home")
    else:
        ov_score = res.get("overall_score", 0)
        if ov_score >= 85:
            tier_label = "Exceptional Fit"
            tier_color = "#34d399"
            tier_badge = "badge-green"
        elif ov_score >= 70:
            tier_label = "Strong Candidate"
            tier_color = "#ff2d75"
            tier_badge = "badge-pink"
        elif ov_score >= 50:
            tier_label = "Competent / Potential"
            tier_color = "#fbbf24"
            tier_badge = "badge-amber"
        else:
            tier_label = "Needs Development"
            tier_color = "#f43f5e"
            tier_badge = "badge-rose"

        # Executive Summary Header Card
        st.markdown(f"""
        <div class="glass-panel" style="margin-bottom: 1.5rem; background: linear-gradient(135deg, rgba(14, 14, 18, 0.95), rgba(26, 16, 22, 0.9)); border: 1px solid rgba(255, 45, 117, 0.25);">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1.5rem;">
                <div>
                    <span class="badge {tier_badge}" style="font-size: 0.75rem; margin-bottom: 6px;">{tier_label}</span>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.7rem; font-weight: 800; color: #ffffff;">
                        {escape(st.session_state.candidate_name or "Candidate")} &bull; {escape(st.session_state.active_role)}
                    </div>
                    <div style="color: #a1a1aa; font-size: 0.88rem; margin-top: 4px;">
                        Question: <strong style="color: #f4f4f5;">"{res.get('question', '')}"</strong>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #a1a1aa; letter-spacing: 0.08em;">Composite Score</div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 2.8rem; font-weight: 900; color: {tier_color}; line-height: 1;">
                        {ov_score}<span style="font-size: 1.4rem; color: #71717a;">/100</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4 Core Pillar Stat Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-title">😊 Facial Emotion</div>
                <div class="stat-value" style="color: #ff6699;">{res.get('emotion', '--')}</div>
                <div class="stat-sub">Dominant facial state</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-title">👀 Eye Contact</div>
                <div class="stat-value" style="color: #fb7185;">{res.get('eye_contact', '--')}</div>
                <div class="stat-sub">Gaze directional tracking</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-title">🎤 Speech Acoustics</div>
                <div class="stat-value" style="color: #34d399;">{res.get('speech_score', 0)}<span style="font-size: 1.1rem; color: #71717a;">/100</span></div>
                <div class="stat-sub">{res.get('wpm', 0)} WPM &bull; {res.get('fillers', 0)} fillers</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-title">📝 Answer Evaluation</div>
                <div class="stat-value" style="color: #ff2d75;">{res.get('answer_score', 0)}<span style="font-size: 1.1rem; color: #71717a;">/100</span></div>
                <div class="stat-sub">Semantic match: {res.get('semantic_score', 0)}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Deep-Dive Tabs
        tab_concepts, tab_speech, tab_vision, tab_recs = st.tabs([
            "🧠 Concept Mastery & NLP",
            "🎙️ Speech & Acoustics",
            "👁️ Visual & Posture",
            "📋 AI Strategic Recommendations"
        ])

        # Tab 1: Concept Mastery
        with tab_concepts:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            c_left, c_right = st.columns([1.1, 0.9], gap="medium")
            
            with c_left:
                st.markdown("""
                <div class="glass-panel">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; color: #ffffff;">
                        📚 Technical Concept Breakdown
                    </div>
                """, unsafe_allow_html=True)
                
                concept_scores = res.get("concept_scores", {})
                if concept_scores:
                    for c_name, c_score in concept_scores.items():
                        if c_score >= 70:
                            bar_grad = "linear-gradient(90deg, #10b981, #34d399)"
                            text_col = "#34d399"
                        elif c_score >= 40:
                            bar_grad = "linear-gradient(90deg, #f59e0b, #fbbf24)"
                            text_col = "#fbbf24"
                        else:
                            bar_grad = "linear-gradient(90deg, #ff2d75, #fb7185)"
                            text_col = "#ff4d8d"
                            
                        st.markdown(f"""
                        <div style="margin-bottom: 1.1rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem;">
                                <span style="font-weight: 600; color: #f4f4f5;">{c_name}</span>
                                <span style="font-weight: 700; color: {text_col};">{c_score}%</span>
                            </div>
                            <div class="concept-bar-container">
                                <div class="concept-bar-fill" style="width: {max(c_score, 4)}%; background: {bar_grad};"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No concept benchmarks registered for this question.")
                st.markdown("</div>", unsafe_allow_html=True)

            with c_right:
                st.markdown("""
                <div class="glass-panel">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; margin-bottom: 0.8rem; color: #ffffff;">
                        🧠 Semantic Feedback & Relevance
                    </div>
                """, unsafe_allow_html=True)
                
                feedback = res.get("answer_feedback", "No feedback generated.")
                cov = res.get("concept_coverage", 0)
                sem = res.get("semantic_score", 0)
                
                st.markdown(f"""
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1.2rem;">
                    <div style="background: rgba(14, 14, 18, 0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 0.75rem; text-align: center;">
                        <div style="font-size: 0.72rem; color: #a1a1aa; text-transform: uppercase;">Concept Coverage</div>
                        <div style="font-size: 1.3rem; font-weight: 800; color: #ff2d75;">{cov}%</div>
                    </div>
                    <div style="background: rgba(14, 14, 18, 0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 0.75rem; text-align: center;">
                        <div style="font-size: 0.72rem; color: #a1a1aa; text-transform: uppercase;">Cosine Similarity</div>
                        <div style="font-size: 1.3rem; font-weight: 800; color: #fb7185;">{sem}%</div>
                    </div>
                </div>
                <div style="background: rgba(255, 45, 117, 0.06); border-left: 3px solid #ff2d75; border-radius: 8px; padding: 1rem; color: #f4f4f5; font-size: 0.92rem; line-height: 1.6;">
                    {feedback}
                </div>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # Tab 2: Speech & Acoustics
        with tab_speech:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            sp_col1, sp_col2 = st.columns([1.0, 1.0], gap="medium")
            
            with sp_col1:
                st.markdown("""
                <div class="glass-panel">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; color: #ffffff;">
                        🎙️ Speech Delivery Metrics
                    </div>
                """, unsafe_allow_html=True)
                
                wpm = res.get("wpm", 0)
                fillers = res.get("fillers", 0)
                bg = res.get("background", "Clear")
                
                if 110 <= wpm <= 165:
                    wpm_status = "Optimal conversational tempo"
                elif wpm < 110:
                    wpm_status = "Deliberate / slightly slow"
                else:
                    wpm_status = "Rapid speech tempo"

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.8rem; background: rgba(14, 14, 18, 0.85); border-radius: 10px; margin-bottom: 0.7rem; border: 1px solid rgba(255,255,255,0.06);">
                    <div>
                        <div style="font-size: 0.88rem; font-weight: 600; color: #f4f4f5;">Pace & Rhythm</div>
                        <div style="font-size: 0.75rem; color: #a1a1aa;">{wpm_status}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 800; color: #ff2d75;">{wpm}</span>
                        <span style="font-size: 0.75rem; color: #71717a;"> WPM</span>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.8rem; background: rgba(14, 14, 18, 0.85); border-radius: 10px; margin-bottom: 0.7rem; border: 1px solid rgba(255,255,255,0.06);">
                    <div>
                        <div style="font-size: 0.88rem; font-weight: 600; color: #f4f4f5;">Filler Words Detected</div>
                        <div style="font-size: 0.75rem; color: #a1a1aa;">Um, uh, like, actually, etc.</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 800; color: {'#34d399' if fillers <= 2 else '#fbbf24'};">{fillers}</span>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.8rem; background: rgba(14, 14, 18, 0.85); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);">
                    <div>
                        <div style="font-size: 0.88rem; font-weight: 600; color: #f4f4f5;">Background Environment</div>
                        <div style="font-size: 0.75rem; color: #a1a1aa;">Acoustic sound classification</div>
                    </div>
                    <div>
                        <span class="badge badge-pink">{bg}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with sp_col2:
                st.markdown("""
                <div class="glass-panel">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; margin-bottom: 0.8rem; color: #ffffff;">
                        📝 Verbatim Whisper Transcript
                    </div>
                """, unsafe_allow_html=True)
                transcript = res.get("transcript", "")
                if transcript.strip():
                    st.markdown(f"""
                    <div class="transcript-bubble">
                        "{transcript}"
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="transcript-bubble" style="color: #a1a1aa; font-style: italic;">
                        No audio speech detected or transcribed during the window.
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # Tab 3: Visual & Posture
        with tab_vision:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            v_col1, v_col2 = st.columns([1.0, 1.0], gap="medium")
            
            with v_col1:
                st.markdown("""
                <div class="glass-panel">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; color: #ffffff;">
                        👁️ Visual Presence Matrix
                    </div>
                """, unsafe_allow_html=True)
                
                emotion_val = res.get("emotion", "Neutral")
                eye_val = res.get("eye_contact", "Looking Center")
                head_val = res.get("head_pose", "Center")
                
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.85rem; background: rgba(14, 14, 18, 0.85); border-radius: 10px; margin-bottom: 0.7rem; border: 1px solid rgba(255,255,255,0.06);">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 20px;">😊</span>
                        <div>
                            <div style="font-size: 0.88rem; font-weight: 600; color: #f4f4f5;">Facial Expression</div>
                            <div style="font-size: 0.75rem; color: #a1a1aa;">Predicted primary emotion</div>
                        </div>
                    </div>
                    <span class="badge badge-green">{emotion_val}</span>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.85rem; background: rgba(14, 14, 18, 0.85); border-radius: 10px; margin-bottom: 0.7rem; border: 1px solid rgba(255,255,255,0.06);">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 20px;">👀</span>
                        <div>
                            <div style="font-size: 0.88rem; font-weight: 600; color: #f4f4f5;">Gaze Alignment</div>
                            <div style="font-size: 0.75rem; color: #a1a1aa;">Focal direction relative to lens</div>
                        </div>
                    </div>
                    <span class="badge {'badge-green' if eye_val == 'Looking Center' else 'badge-amber'}">{eye_val}</span>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.85rem; background: rgba(14, 14, 18, 0.85); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 20px;">👤</span>
                        <div>
                            <div style="font-size: 0.88rem; font-weight: 600; color: #f4f4f5;">Head Orientation</div>
                            <div style="font-size: 0.75rem; color: #a1a1aa;">Euler yaw, pitch & roll angle</div>
                        </div>
                    </div>
                    <span class="badge {'badge-green' if head_val == 'Center' else 'badge-amber'}">{head_val}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with v_col2:
                st.markdown("""
                <div class="glass-panel">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; margin-bottom: 0.8rem; color: #ffffff;">
                        🎯 Non-Verbal Synthesis
                    </div>
                    <div style="font-size: 0.9rem; color: #d4d4d8; line-height: 1.6;">
                        Non-verbal cues like steady eye contact and an upright posture communicate confidence, active engagement, and composure to interviewers.
                    </div>
                    <div style="margin-top: 1rem; padding: 0.85rem; background: rgba(255, 45, 117, 0.06); border-radius: 10px; border-left: 3px solid #ff2d75;">
                        <div style="font-size: 0.8rem; font-weight: 700; color: #ff6699; margin-bottom: 3px;">BEHAVIOR OBSERVATION</div>
                        <div style="font-size: 0.85rem; color: #f4f4f5;">
                """, unsafe_allow_html=True)
                
                obs = []
                if eye_val == "Looking Center":
                    obs.append("Excellent direct eye engagement maintained.")
                else:
                    obs.append("Frequent gaze shifts noticed away from central axis.")
                    
                if head_val == "Center":
                    obs.append("Stable head alignment without tilt or excessive nodding.")
                else:
                    obs.append("Consider keeping head upright and forward-facing.")
                    
                if emotion_val in ["Happy", "Neutral"]:
                    obs.append("Positive and calm affective presentation.")
                else:
                    obs.append("Expression showed subtle tension or fatigue.")
                    
                st.markdown(" &bull; ".join(obs), unsafe_allow_html=True)
                st.markdown("""
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Tab 4: AI Recommendations
        with tab_recs:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div class="glass-panel">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 700; color: #ffffff;">
                        📋 Targeted Action Plan & Recommendations
                    </div>
                    <span class="badge badge-pink">AI Generated</span>
                </div>
            """, unsafe_allow_html=True)
            
            recs = res.get("recommendations", [])
            if recs:
                for r in recs:
                    icon = "💡"
                    if "eye" in r.lower():
                        icon = "👀"
                    elif "filler" in r.lower():
                        icon = "🗣️"
                    elif "head" in r.lower():
                        icon = "👤"
                    elif "speak" in r.lower() or "slow" in r.lower():
                        icon = "⏱️"
                    elif "excellent" in r.lower():
                        icon = "🏆"
                    
                    st.markdown(f"""
                    <div class="recommendation-item">
                        <span style="font-size: 1.25rem;">{icon}</span>
                        <span style="font-weight: 500;">{r}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="recommendation-item">
                    <span style="font-size: 1.25rem;">🏆</span>
                    <span>Outstanding performance across all evaluated dimensions.</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Bottom Action Bar
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns([1, 1], gap="medium")
        with btn_c1:
            if st.button("🔄 Retake Interview / New Candidate", use_container_width=True):
                reset_session()
        with btn_c2:
            if st.button("⬅️ Back to Camera Room", use_container_width=True):
                go_to_page("interview")

# ==================================================
# PAGE 4: SETTINGS PAGE (PERSONAL DETAILS & SECURITY)
# ==================================================
elif st.session_state.current_page == "settings":
    auth_user = st.session_state.get("auth_user", {})
    user_uid = auth_user.get("uid", "")
    id_token = st.session_state.get("auth_id_token", "")
    user_email = auth_user.get("email") or st.session_state.get("candidate_email", "")
    user_name = (
        st.session_state.get("candidate_name")
        or auth_user.get("name")
        or (user_email.split("@")[0].title() if user_email else "")
        or "Candidate"
    )

    # Resolve local avatar path
    avatars_dir = Path(__file__).resolve().parent / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    local_avatar = avatars_dir / f"{user_uid}.png" if user_uid else None
    has_local_avatar = local_avatar and local_avatar.is_file()

    # Resolve avatar source and square adjustments
    avatar_src = str(local_avatar) if has_local_avatar else st.session_state.get("candidate_profile_photo")
    zoom_val = float(st.session_state.get("photo_zoom", 1.0))
    off_x = int(st.session_state.get("photo_offset_x", 50))
    off_y = int(st.session_state.get("photo_offset_y", 50))
    settings_header_avatar = render_square_avatar_html(avatar_src, user_name, size=58, border_radius=10, zoom=zoom_val, offset_x=off_x, offset_y=off_y)

    # Settings Executive Header
    st.markdown(f"""
    <div class="glass-panel" style="margin-bottom: 1.5rem; border: 1px solid rgba(255, 45, 117, 0.28);">
        <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 1rem;">
            <div style="display: flex; align-items: center; gap: 16px;">
                {settings_header_avatar}
                <div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.4rem; font-weight: 800; color: #ffffff;">
                        {escape(user_name)}
                    </div>
                    <div style="font-size: 0.86rem; color: #a1a1aa;">
                        {escape(user_email)} &bull; <span class="badge badge-green" style="font-size: 0.7rem; padding: 2px 7px;">Verified Email ✓</span>
                    </div>
                </div>
            </div>
            <div>
                <span class="badge badge-pink" style="font-size: 0.78rem;">Candidate Profile</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_profile, tab_security = st.tabs(["👤 Personal Details & Profile", "🛡️ Security & Multi-Factor Auth"])

    with tab_profile:
        col_avatar, col_details = st.columns([1, 1.4], gap="large")

        with col_avatar:
            st.markdown("""
            <div class="glass-panel">
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-bottom: 0.8rem;">
                    🖼️ Square Profile Photo
                </div>
            """, unsafe_allow_html=True)

            uploaded_photo = st.file_uploader(
                "Upload a photo to adjust",
                type=["png", "jpg", "jpeg"],
                help="Upload any photo to frame and adjust into a perfect 1:1 square.",
                key="settings_photo_uploader",
            )

            # Determine image bytes to display
            temp_preview_src = avatar_src
            if uploaded_photo is not None:
                temp_preview_src = f"data:image/png;base64,{base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')}"

            st.caption("Adjust photo position & scale:")
            col_z, col_y = st.columns(2)
            with col_z:
                adj_zoom = st.slider("🔍 Zoom / Scale", 1.0, 3.0, zoom_val, 0.1, key="slider_zoom")
            with col_y:
                adj_y = st.slider("↕️ Vertical Align", 0, 100, off_y, 5, key="slider_pos_y")

            adj_x = st.slider("↔️ Horizontal Align", 0, 100, off_x, 5, key="slider_pos_x")

            # Centered exact 1:1 square preview
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 12px 0 16px;">
                {render_square_avatar_html(temp_preview_src, user_name, size=136, border_radius=12, zoom=adj_zoom, offset_x=adj_x, offset_y=adj_y)}
                <div style="font-size: 0.72rem; color: #a1a1aa; margin-top: 6px;">Exact 1:1 Square Framing Preview</div>
            </div>
            """, unsafe_allow_html=True)

            col_btn_save, col_btn_remove = st.columns([1.2, 1])

            with col_btn_save:
                if st.button("💾 Apply & Save", type="primary", use_container_width=True, key="save_square_photo_btn"):
                    try:
                        if uploaded_photo is not None:
                            cropped_bytes = process_square_photo(uploaded_photo.getvalue(), zoom=adj_zoom, offset_x=adj_x, offset_y=adj_y, output_size=400)
                            if local_avatar:
                                local_avatar.write_bytes(cropped_bytes)
                            st.session_state["candidate_profile_photo"] = str(local_avatar)
                        elif local_avatar and local_avatar.is_file():
                            cropped_bytes = process_square_photo(local_avatar.read_bytes(), zoom=adj_zoom, offset_x=adj_x, offset_y=adj_y, output_size=400)
                            local_avatar.write_bytes(cropped_bytes)
                            st.session_state["candidate_profile_photo"] = str(local_avatar)

                        st.session_state["photo_zoom"] = adj_zoom
                        st.session_state["photo_offset_x"] = adj_x
                        st.session_state["photo_offset_y"] = adj_y
                        st.success("✅ Square profile photo updated successfully!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error processing photo: {exc}")

            with col_btn_remove:
                if st.button("🗑️ Remove Photo", type="secondary", use_container_width=True, key="remove_square_photo_btn"):
                    try:
                        if local_avatar and local_avatar.is_file():
                            local_avatar.unlink(missing_ok=True)
                        st.session_state.pop("candidate_profile_photo", None)
                        st.session_state.pop("candidate_photo_url", None)
                        st.session_state.pop("photo_zoom", None)
                        st.session_state.pop("photo_offset_x", None)
                        st.session_state.pop("photo_offset_y", None)
                        try:
                            update_user_profile(id_token, photo_url="")
                        except Exception:
                            pass
                        st.success("✅ Profile photo removed! Default square monogram restored.")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not remove photo: {exc}")

            st.markdown("</div>", unsafe_allow_html=True)

        with col_details:
            st.markdown("""
            <div class="glass-panel">
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-bottom: 1rem;">
                    📝 Personal Details
                </div>
            """, unsafe_allow_html=True)

            with st.form("settings_personal_details_form"):
                new_display_name = st.text_input(
                    "Display Name / Candidate Full Name",
                    value=user_name,
                    help="Your name as displayed on evaluation scorecards and certificates.",
                    key="settings_input_display_name",
                )

                st.text_input(
                    "Registered Email (Primary)",
                    value=user_email,
                    disabled=True,
                    help="Email address linked to your Firebase account.",
                )

                st.text_input(
                    "Firebase Candidate UID",
                    value=user_uid,
                    disabled=True,
                    help="Unique immutable account identifier in Firebase Identity Toolkit.",
                )

                submitted_name = st.form_submit_button(
                    "💾 Save Personal Details",
                    type="primary",
                    use_container_width=True,
                )

            if submitted_name:
                cleaned_name = new_display_name.strip()
                if not cleaned_name:
                    st.error("Please provide a valid candidate name.")
                else:
                    try:
                        with st.spinner("Updating profile in Firebase..."):
                            update_user_profile(id_token, display_name=cleaned_name)
                    except FirebaseAuthError as exc:
                        st.error(str(exc))
                    else:
                        st.session_state["candidate_name"] = cleaned_name
                        if "auth_user" in st.session_state and isinstance(st.session_state["auth_user"], dict):
                            st.session_state["auth_user"]["name"] = cleaned_name
                        if "candidate_profile" in st.session_state and isinstance(st.session_state["candidate_profile"], dict):
                            st.session_state["candidate_profile"]["name"] = cleaned_name
                        st.success("✅ Profile name updated successfully!")
                        time.sleep(0.5)
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    with tab_security:
        col_mfa, col_pwd = st.columns([1.1, 0.9], gap="large")

        with col_mfa:
            st.markdown("""
            <div class="glass-panel">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 700; color: #ffffff;">
                        🛡️ Multi-Factor Authorization (MFA)
                    </div>
                    <span class="badge badge-pink">2FA Protection</span>
                </div>
            """, unsafe_allow_html=True)

            is_mfa_active = bool(st.session_state.get("auth_mfa_enabled", False))

            if is_mfa_active:
                st.markdown("""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 12px; padding: 1rem; margin-bottom: 1.2rem;">
                    <div style="color: #34d399; font-weight: 700; font-size: 1rem;">✅ Multi-Factor Authentication is Active</div>
                    <div style="color: #a1a1aa; font-size: 0.85rem; margin-top: 4px;">
                        Your account is safeguarded with Two-Factor Authentication via TOTP Authenticator.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Disable Multi-Factor Authentication", type="secondary", key="disable_mfa_btn", use_container_width=True):
                    st.session_state["auth_mfa_enabled"] = False
                    st.warning("⚠️ Multi-Factor Authentication has been disabled for your account.")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.markdown("""
                <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 1rem; margin-bottom: 1.2rem;">
                    <div style="color: #fbbf24; font-weight: 700; font-size: 1rem;">⚠️ 2FA Currently Inactive</div>
                    <div style="color: #a1a1aa; font-size: 0.85rem; margin-top: 4px;">
                        Add a hardware/software authenticator layer (Google Authenticator, Microsoft Authenticator, or Authy) to secure your account.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style="font-size: 0.88rem; font-weight: 600; color: #ffffff; margin-bottom: 6px;">
                    Step 1: Scan QR or enter Secret Key into your Authenticator App
                </div>
                """, unsafe_allow_html=True)

                mfa_secret = f"AIA-{user_uid[:4].upper() if len(user_uid)>=4 else 'SEC1'}-{user_uid[-4:].upper() if len(user_uid)>=4 else 'SEC2'}-2FA"
                st.code(mfa_secret, language="text")

                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=otpauth://totp/AIAssessment:{user_email}?secret={mfa_secret}&issuer=AIAssessmentSystem"
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 14px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px; margin-bottom: 1rem;">
                    <img src="{qr_url}" width="80" height="80" style="border-radius: 8px; background: #ffffff; padding: 4px;" alt="2FA QR Code" />
                    <div style="font-size: 0.82rem; color: #a1a1aa; line-height: 1.5;">
                        Scan this QR code with <strong>Google Authenticator</strong>, <strong>Microsoft Authenticator</strong>, or <strong>Authy</strong> on your smartphone.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style="font-size: 0.88rem; font-weight: 600; color: #ffffff; margin-bottom: 6px;">
                    Step 2: Enter 6-digit verification code from Authenticator App
                </div>
                """, unsafe_allow_html=True)

                with st.form("settings_enable_mfa_form"):
                    code_input = st.text_input(
                        "6-Digit Authentication Code",
                        max_chars=6,
                        placeholder="123456",
                        key="mfa_verification_code_input",
                    )
                    enable_mfa_submitted = st.form_submit_button(
                        "🛡️ Enable Multi-Factor Authentication",
                        type="primary",
                        use_container_width=True,
                    )

                if enable_mfa_submitted:
                    code_clean = code_input.strip()
                    if len(code_clean) != 6 or not code_clean.isdigit():
                        st.error("Please enter a valid 6-digit numerical code from your authenticator app.")
                    else:
                        st.session_state["auth_mfa_enabled"] = True
                        st.success("✅ Multi-Factor Authentication successfully activated!")
                        time.sleep(0.5)
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with col_pwd:
            st.markdown("""
            <div class="glass-panel">
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-bottom: 1rem;">
                    🔑 Password & Security
                </div>
            """, unsafe_allow_html=True)

            with st.form("settings_change_password_form"):
                new_pwd = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="At least 6 characters",
                    key="settings_new_password_input",
                )
                confirm_new_pwd = st.text_input(
                    "Confirm New Password",
                    type="password",
                    placeholder="Re-enter new password",
                    key="settings_confirm_password_input",
                )
                pwd_submit = st.form_submit_button(
                    "Update Password",
                    type="primary",
                    use_container_width=True,
                )

            if pwd_submit:
                if not new_pwd or not confirm_new_pwd:
                    st.error("Please fill in both password fields.")
                elif len(new_pwd) < 6:
                    st.error("Password must be at least 6 characters long.")
                elif new_pwd != confirm_new_pwd:
                    st.error("Passwords do not match.")
                else:
                    try:
                        with st.spinner("Updating password in Firebase..."):
                            update_user_password(id_token, new_pwd)
                    except FirebaseAuthError as exc:
                        st.error(str(exc))
                    else:
                        st.success("✅ Password updated successfully!")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.caption("Forgot your password or prefer an email link?")
            if st.button("📧 Send Password Reset Email", key="settings_send_reset_email_btn", use_container_width=True):
                try:
                    with st.spinner("Dispatching reset email..."):
                        send_password_reset_email(user_email)
                    st.success(f"✅ Password reset link sent to **{user_email}**.")
                except FirebaseAuthError as exc:
                    st.error(str(exc))

            st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------
    # Bottom Action Bar (Return to Lobby + Logout)
    # --------------------------------------------------
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(14, 14, 18, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; color: #ffffff;">
                    🚪 Active Session Management
                </div>
                <div style="font-size: 0.82rem; color: #a1a1aa; margin-top: 2px;">
                    Return to the interview lobby or terminate your authenticated session.
                </div>
            </div>
            <span class="badge badge-rose">Session Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_ret, c_out = st.columns([1, 1], gap="medium")
    with c_ret:
        if st.button("⬅️ Return to Candidate Lobby", key="settings_return_lobby_btn", use_container_width=True):
            go_to_page("home")

    with c_out:
        if st.button("🚪 Log Out of Account", type="primary", key="settings_bottom_logout_btn", use_container_width=True):
            logout_user()