import streamlit as st
import os
import time
from datetime import datetime
from dotenv import load_dotenv

import database as db
import evaluator

# ─── PAGE CONFIG ──────────────────────────────────────────────────
st.set_page_config(
    page_title="EMRS ESSE Exam Portal",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# ─── ENVIRONMENT ─────────────────────────────────────────────────
# Works for both local (.env) and Streamlit Cloud (st.secrets)
def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

GOOGLE_CLIENT_ID     = get_secret("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET")
GEMINI_API_KEY       = get_secret("GEMINI_API_KEY")
ADMIN_EMAILS         = [e.strip() for e in get_secret("ADMIN_EMAILS", "").split(",") if e.strip()]
REDIRECT_URI         = get_secret("REDIRECT_URI", "http://localhost:8501")
# Expose DATABASE_URL to environment so database.py can read it
os.environ["DATABASE_URL"] = get_secret("DATABASE_URL", "")

# ─── INIT ─────────────────────────────────────────────────────────
db.init_db()
if GEMINI_API_KEY:
    evaluator.configure_gemini(GEMINI_API_KEY)

# ─── MASTER CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --navy:      #0a0f1e;
    --navy2:     #0f1729;
    --navy3:     #162040;
    --gold:      #f0c060;
    --gold2:     #e8a020;
    --teal:      #00d4aa;
    --teal2:     #00a884;
    --text:      #e8eaf0;
    --text-dim:  #8892a4;
    --border:    rgba(240,192,96,0.18);
    --card-bg:   rgba(15,23,41,0.95);
    --glass:     rgba(255,255,255,0.04);
}

html, body, [data-testid="stApp"] {
    background-color: var(--navy) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #0f1729 60%, #0d1a3a 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stRadio label {
    background: var(--glass);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 1rem !important;
    margin: 3px 0 !important;
    transition: all 0.2s;
    cursor: pointer;
    display: block;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(240,192,96,0.1) !important;
    border-color: var(--gold) !important;
}

.main .block-container { background: transparent !important; padding-top: 1rem !important; }

.hero-banner {
    background: linear-gradient(135deg, #0d1a3a 0%, #162040 40%, #1a2a50 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    text-align: center;
}
.hero-banner::before {
    content: '';
    position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(ellipse at 60% 40%, rgba(240,192,96,0.07) 0%, transparent 60%),
                radial-gradient(ellipse at 20% 80%, rgba(0,212,170,0.05) 0%, transparent 50%);
    pointer-events: none;
}
.hero-banner h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 2.6rem !important; font-weight: 900 !important;
    color: var(--gold) !important; margin: 0 0 0.4rem !important;
    text-shadow: 0 0 40px rgba(240,192,96,0.3);
}
.hero-banner .subtitle { color: var(--text-dim) !important; font-size: 1rem; letter-spacing: 1px; text-transform: uppercase; }
.hero-banner .badge {
    display: inline-block;
    background: rgba(240,192,96,0.12); border: 1px solid rgba(240,192,96,0.3);
    color: var(--gold); border-radius: 20px; padding: 0.25rem 1rem;
    font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 1rem;
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem; color: var(--gold);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem; margin-bottom: 1.2rem;
}

.question-card {
    background: linear-gradient(135deg, #0f1729 0%, #162040 100%);
    border: 1px solid var(--border); border-left: 4px solid var(--gold);
    border-radius: 12px; padding: 1.5rem 1.8rem; margin-bottom: 1.2rem;
}
.question-card .q-number {
    display: inline-block; background: var(--gold); color: var(--navy);
    font-weight: 700; font-size: 0.75rem; padding: 0.2rem 0.7rem;
    border-radius: 20px; margin-bottom: 0.7rem; letter-spacing: 1px; text-transform: uppercase;
}
.question-card .q-text { color: var(--text) !important; font-size: 1.05rem; line-height: 1.6; }
.question-card .q-marks { color: var(--teal); font-size: 0.85rem; margin-top: 0.5rem; }
.question-card .q-hint { color: var(--text-dim); font-size: 0.85rem; font-style: italic; margin-top: 0.4rem; }

.rank-card {
    background: linear-gradient(135deg, #0f1729 0%, #162040 100%);
    border: 1px solid var(--border); border-radius: 12px;
    padding: 1rem 1.5rem; margin-bottom: 0.6rem;
    display: flex; align-items: center; gap: 1.2rem;
    transition: transform 0.2s, border-color 0.2s;
}
.rank-card:hover { transform: translateX(4px); }
.rank-1 { border-left: 5px solid #FFD700; box-shadow: 0 0 20px rgba(255,215,0,0.15); }
.rank-2 { border-left: 5px solid #C0C0C0; box-shadow: 0 0 15px rgba(192,192,192,0.1); }
.rank-3 { border-left: 5px solid #CD7F32; box-shadow: 0 0 15px rgba(205,127,50,0.1); }
.rank-medal { font-size: 2rem; min-width: 2.5rem; text-align: center; }
.rank-name { color: var(--text) !important; font-weight: 600; font-size: 1.05rem; }
.rank-email { color: var(--text-dim) !important; font-size: 0.82rem; }
.rank-score { text-align: right; }
.rank-score .score-val { color: var(--gold) !important; font-size: 1.3rem; font-weight: 700; }
.rank-score .score-pct { color: var(--teal) !important; font-size: 0.85rem; }
.score-bar-bg {
    background: rgba(255,255,255,0.08); border-radius: 10px;
    height: 5px; width: 120px; display: inline-block; overflow: hidden; margin-top: 4px;
}
.score-bar-fill { height: 100%; border-radius: 10px; background: linear-gradient(90deg, var(--teal2), var(--gold)); }

.feedback-box {
    background: rgba(0,212,170,0.08); border: 1px solid rgba(0,212,170,0.25);
    border-radius: 10px; padding: 1rem 1.2rem; margin-top: 0.8rem;
    color: #a0f0e0 !important; font-size: 0.92rem; line-height: 1.6;
}
.feedback-box .fb-label {
    color: var(--teal) !important; font-weight: 600; font-size: 0.8rem;
    letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.3rem;
}

.stat-card {
    background: linear-gradient(135deg, #0f1729, #162040);
    border: 1px solid var(--border); border-radius: 12px;
    padding: 1.2rem 1.5rem; text-align: center;
}
.stat-card .stat-val {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem; color: var(--gold); font-weight: 700; display: block;
}
.stat-card .stat-label { color: var(--text-dim); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }

.login-container {
    max-width: 480px; margin: 2rem auto;
    background: linear-gradient(135deg, #0f1729 0%, #162040 100%);
    border: 1px solid var(--border); border-radius: 20px; padding: 3rem;
    text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.login-logo { font-size: 4rem; margin-bottom: 1rem; display: block; }
.login-title { font-family: 'Playfair Display', serif; font-size: 1.8rem; color: var(--gold); margin-bottom: 0.4rem; }
.login-subtitle { color: var(--text-dim); font-size: 0.9rem; margin-bottom: 2rem; line-height: 1.6; }
.feature-row { display: flex; gap: 0.8rem; margin: 1.2rem 0; text-align: left; }
.feature-item {
    flex: 1; background: rgba(255,255,255,0.03);
    border: 1px solid var(--border); border-radius: 10px;
    padding: 0.8rem; font-size: 0.8rem; color: var(--text-dim);
}
.feature-item .fi-icon { font-size: 1.3rem; margin-bottom: 0.3rem; display: block; }
.feature-item .fi-text { color: var(--text); font-weight: 500; display: block; }

.admin-stat {
    background: linear-gradient(135deg, #0f1729, #1a2a50);
    border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.2rem; margin-bottom: 0.5rem;
    display: flex; justify-content: space-between; align-items: center;
}
.as-title { color: var(--text); font-weight: 500; }
.as-badge { padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.badge-active { background: rgba(0,212,170,0.15); color: var(--teal); border: 1px solid rgba(0,212,170,0.3); }
.badge-closed { background: rgba(255,255,255,0.05); color: var(--text-dim); border: 1px solid rgba(255,255,255,0.1); }

.profile-box {
    background: rgba(240,192,96,0.07); border: 1px solid var(--border);
    border-radius: 12px; padding: 1rem; text-align: center; margin-bottom: 1rem;
}
.profile-name { color: var(--gold) !important; font-weight: 600; font-size: 1rem; }
.profile-email { color: var(--text-dim) !important; font-size: 0.78rem; }
.admin-badge {
    display: inline-block;
    background: linear-gradient(135deg, var(--gold2), var(--gold));
    color: var(--navy); font-size: 0.72rem; font-weight: 700;
    letter-spacing: 1px; padding: 0.2rem 0.7rem; border-radius: 20px;
    text-transform: uppercase; margin-top: 0.3rem;
}

/* Streamlit component overrides */
.stTextArea textarea {
    background: #0f1729 !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.95rem !important;
}
.stTextArea textarea:focus { border-color: var(--gold) !important; box-shadow: 0 0 0 2px rgba(240,192,96,0.15) !important; }
.stTextInput input {
    background: #0f1729 !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 8px !important;
}
.stTextInput input:focus { border-color: var(--gold) !important; }
.stNumberInput input { background: #0f1729 !important; border: 1px solid var(--border) !important; color: var(--text) !important; }

.stButton > button {
    background: linear-gradient(135deg, var(--gold2), var(--gold)) !important;
    color: var(--navy) !important; border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-family: 'DM Sans', sans-serif !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(240,192,96,0.35) !important; }
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, var(--gold2), var(--gold)) !important;
    color: var(--navy) !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important;
}

[data-testid="stTabs"] [role="tablist"] {
    background: rgba(15,23,41,0.8) !important; border-radius: 10px !important;
    padding: 4px !important; border: 1px solid var(--border) !important; gap: 4px !important;
}
[data-testid="stTabs"] button[role="tab"] { color: var(--text-dim) !important; border-radius: 7px !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, var(--gold2), var(--gold)) !important;
    color: var(--navy) !important; font-weight: 700 !important;
}

[data-testid="stExpander"] { background: #0f1729 !important; border: 1px solid var(--border) !important; border-radius: 10px !important; }
[data-testid="stExpander"] summary { color: var(--text) !important; }
[data-testid="stExpander"] summary:hover { color: var(--gold) !important; }

[data-testid="stMetric"] { background: linear-gradient(135deg, #0f1729, #162040) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; padding: 1rem !important; }
[data-testid="stMetricValue"] { color: var(--gold) !important; }
[data-testid="stMetricLabel"] { color: var(--text-dim) !important; }

[data-testid="stAlert"] { background: rgba(240,192,96,0.07) !important; border: 1px solid rgba(240,192,96,0.2) !important; color: var(--text) !important; border-radius: 10px !important; }
hr { border-color: var(--border) !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 10px !important; }
label, .stMarkdown p, p { color: var(--text) !important; }
small { color: var(--text-dim) !important; }
h1, h2, h3, h4 { color: var(--gold) !important; font-family: 'Playfair Display', serif !important; }
[data-testid="stProgressBar"] > div { background: var(--navy3) !important; }
[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg, var(--teal2), var(--gold)) !important; }
.stCaption { color: var(--text-dim) !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  GOOGLE OAUTH
# ══════════════════════════════════════════════════════════════════
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

def get_google_auth_url():
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {"web": {
            "client_id": GOOGLE_CLIENT_ID, "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }},
        scopes=SCOPES,
    )
    flow.redirect_uri = REDIRECT_URI
    auth_url, state = flow.authorization_url(access_type="offline", prompt="select_account")
    st.session_state["oauth_state"] = state
    return auth_url, flow

def exchange_code_for_user(code):
    from google_auth_oauthlib.flow import Flow
    import requests as req
    flow = Flow.from_client_config(
        {"web": {
            "client_id": GOOGLE_CLIENT_ID, "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }},
        scopes=SCOPES,
        state=st.session_state.get("oauth_state", ""),
    )
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=code)
    credentials = flow.credentials
    userinfo = req.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"}
    ).json()
    return userinfo


# ══════════════════════════════════════════════════════════════════
#  SESSION STATE & OAUTH CALLBACK
# ══════════════════════════════════════════════════════════════════
if "user" not in st.session_state:
    st.session_state.user = None

params = st.query_params
if "code" in params and st.session_state.user is None:
    try:
        with st.spinner("Signing you in..."):
            if REDIRECT_URI.startswith("http://"):
                os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            userinfo = exchange_code_for_user(params["code"])
            email    = userinfo.get("email", "")
            name     = userinfo.get("name", email)
            picture  = userinfo.get("picture", "")
            user     = db.upsert_user(email, name, picture)
            if email in ADMIN_EMAILS and user["role"] != "admin":
                db.set_admin(email)
                user = db.get_user_by_email(email)
            st.session_state.user = user
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")
        st.query_params.clear()


# ══════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ══════════════════════════════════════════════════════════════════
def show_login_page():
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("""
        <div class="login-container">
            <span class="login-logo">📚</span>
            <div class="login-title">EMRS ESSE Portal</div>
            <div class="login-subtitle">
                TGT / PGT Computer Science<br>
                AI-Powered Descriptive Answer Evaluation
            </div>
            <div class="feature-row">
                <div class="feature-item">
                    <span class="fi-icon">🔐</span>
                    <span class="fi-text">Secure Login</span>
                    Google OAuth
                </div>
                <div class="feature-item">
                    <span class="fi-icon">🤖</span>
                    <span class="fi-text">AI Evaluation</span>
                    Gemini 2.5 Flash
                </div>
                <div class="feature-item">
                    <span class="fi-icon">🏆</span>
                    <span class="fi-text">Live Rankings</span>
                    Instant Results
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            st.error("Google OAuth not configured. Check your .env file.")
            return

        if st.button("🔐  Sign in with Google", use_container_width=True, type="primary"):
            try:
                if REDIRECT_URI.startswith("http://"):
                    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
                auth_url, _ = get_google_auth_url()
                st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                st.markdown(f"[Click here if not redirected]({auth_url})")
            except Exception as e:
                st.error(f"OAuth Error: {e}")


# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
def show_sidebar():
    user = st.session_state.user
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:1rem 0 0.5rem;">
            <span style="font-family:'Playfair Display',serif; font-size:1.3rem; color:#f0c060; font-weight:700;">
                📚 EMRS ESSE
            </span>
        </div>
        """, unsafe_allow_html=True)

        pic_html   = f'<img src="{user["picture"]}" width="60" style="border-radius:50%; border:2px solid #f0c060; margin-bottom:0.5rem;"><br>' if user.get("picture") else ""
        admin_html = '<span class="admin-badge">Admin</span>' if user["role"] == "admin" else ""
        st.markdown(f"""
        <div class="profile-box">
            {pic_html}
            <div class="profile-name">{user["name"]}</div>
            <div class="profile-email">{user["email"]}</div>
            {admin_html}
        </div>
        """, unsafe_allow_html=True)

        nav_options = ["📝  Exam", "🏆  Rankings", "👁️  My Results"]
        if user["role"] == "admin":
            nav_options.append("⚙️  Admin Panel")

        page = st.radio("Navigate", nav_options, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚪  Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

        st.markdown("""
        <div style="text-align:center; margin-top:2rem; color:#2a3a5a; font-size:0.75rem;">
            Powered by Gemini 2.5 Flash
        </div>
        """, unsafe_allow_html=True)

    return page


# ══════════════════════════════════════════════════════════════════
#  EXAM PAGE
# ══════════════════════════════════════════════════════════════════
def show_exam_page():
    st.markdown("""
    <div class="hero-banner">
        <div class="badge">Live Exam</div>
        <h1>📝 Answer Sheet</h1>
        <div class="subtitle">Read each question carefully before answering</div>
    </div>
    """, unsafe_allow_html=True)

    session = db.get_active_session()
    if not session:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0f1729,#162040); border:1px solid rgba(240,192,96,0.18);
             border-radius:12px; padding:3rem; text-align:center;">
            <div style="font-size:3rem;">⏳</div>
            <h3>No Active Exam Session</h3>
            <p style="color:#8892a4;">Please wait for the administrator to start a session.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"""
    <div style="background:rgba(0,212,170,0.08); border:1px solid rgba(0,212,170,0.2);
         border-radius:10px; padding:0.8rem 1.2rem; margin-bottom:1.5rem; color:#a0f0e0;">
        <b style="color:#00d4aa;">Session:</b> {session["title"]}
        {"  ·  " + session["description"] if session.get("description") else ""}
    </div>
    """, unsafe_allow_html=True)

    questions = db.get_questions_for_session(session["id"])
    if not questions:
        st.info("Questions not posted yet. Please check back soon.")
        return

    user     = st.session_state.user
    existing = {s["question_id"]: s for s in db.get_user_submissions(user["id"], session["id"])}

    if all(q["id"] in existing for q in questions):
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0f1729,#162040); border:1px solid rgba(0,212,170,0.3);
             border-radius:12px; padding:3rem; text-align:center;">
            <div style="font-size:3rem;">✅</div>
            <h3 style="color:#00d4aa;">All Answers Submitted!</h3>
            <p style="color:#8892a4;">Go to <b>My Results</b> to view your scores once evaluated.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Answer mode selector
    st.markdown("""
    <div style="background:rgba(240,192,96,0.07); border:1px solid rgba(240,192,96,0.18);
         border-radius:10px; padding:0.8rem 1.2rem; margin-bottom:1rem;">
        <b style="color:#f0c060;">Choose Answer Mode</b>
        <p style="color:#8892a4; margin:0.3rem 0 0; font-size:0.88rem;">
            You can type your answers OR upload a photo of your handwritten answers — or mix both!
        </p>
    </div>
    """, unsafe_allow_html=True)

    answers      = {}
    images       = {}
    answer_types = {}

    for i, q in enumerate(questions, 1):
        already   = existing.get(q["id"])
        hint_html = f'<div class="q-hint">Hint: {q["hint"]}</div>' if q.get("hint") else ""
        st.markdown(f"""
        <div class="question-card">
            <span class="q-number">Question {i}</span>
            <div class="q-text">{q["question_text"]}</div>
            <div class="q-marks">Marks: {q["marks"]}</div>
            {hint_html}
        </div>
        """, unsafe_allow_html=True)

        mode_key = f"mode_{q['id']}"
        default_mode = already["answer_type"] if already and already.get("answer_type") else "Type Answer"
        mode = st.radio(
            f"Answer mode for Q{i}",
            ["Type Answer", "Upload Handwritten Image"],
            index=0 if default_mode == "text" else 1,
            key=mode_key,
            horizontal=True,
            label_visibility="collapsed"
        )

        if mode == "Type Answer":
            answer_types[q["id"]] = "text"
            answers[q["id"]] = st.text_area(
                f"Type your answer for Q{i}",
                value=already["answer_text"] if already and already.get("answer_text") else "",
                height=150,
                key=f"ans_{q['id']}",
                placeholder="Write a detailed, well-structured answer using proper technical terminology..."
            )
            images[q["id"]] = None
        else:
            answer_types[q["id"]] = "image"
            answers[q["id"]]  = None
            uploaded = st.file_uploader(
                f"Upload handwritten answer for Q{i}",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"img_{q['id']}",
                help="Take a clear photo of your handwritten answer and upload it here"
            )
            if uploaded:
                images[q["id"]] = uploaded
                st.image(uploaded, caption=f"Q{i} — Uploaded handwritten answer", width=400)
                st.success("Image uploaded successfully!")
            elif already and already.get("answer_image"):
                images[q["id"]] = "existing"
                st.info("Previously uploaded image on record. Upload a new one to replace it.")
            else:
                images[q["id"]] = None

        st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀  Submit All Answers", type="primary", use_container_width=True):
        # Validate all questions have some answer
        missing = []
        for i, q in enumerate(questions, 1):
            atype = answer_types.get(q["id"], "text")
            if atype == "text" and not (answers.get(q["id"]) or "").strip():
                missing.append(f"Q{i}")
            elif atype == "image" and images.get(q["id"]) is None:
                missing.append(f"Q{i}")

        if missing:
            st.error(f"Please answer all questions. Missing: {', '.join(missing)}")
        else:
            for q in questions:
                atype = answer_types.get(q["id"], "text")
                if atype == "text":
                    db.save_answer(
                        user["id"], q["id"], session["id"],
                        answer_text=answers[q["id"]].strip(),
                        answer_type="text"
                    )
                else:
                    img_file = images.get(q["id"])
                    if img_file and img_file != "existing":
                        img_bytes = img_file.read()
                        db.save_answer(
                            user["id"], q["id"], session["id"],
                            answer_image=img_bytes,
                            answer_image_name=img_file.name,
                            answer_type="image"
                        )
                    # if "existing" — skip, keep old image

            st.success("Answers submitted successfully! Evaluation will begin shortly.")
            st.balloons()
            time.sleep(2)
            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  MY RESULTS
# ══════════════════════════════════════════════════════════════════
def show_my_results():
    st.markdown("""
    <div class="hero-banner">
        <div class="badge">Your Performance</div>
        <h1>👁️ My Results</h1>
        <div class="subtitle">Detailed AI evaluation of your answers</div>
    </div>
    """, unsafe_allow_html=True)

    sessions = db.get_all_sessions()
    if not sessions:
        st.info("No exam sessions found.")
        return

    sel = st.selectbox("Select Session", [f"{s['id']} — {s['title']}" for s in sessions])
    sid = int(sel.split("—")[0].strip())

    user = st.session_state.user
    subs = db.get_user_submissions(user["id"], sid)

    if not subs:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0f1729,#162040); border:1px solid rgba(240,192,96,0.18);
             border-radius:12px; padding:2rem; text-align:center;">
            <div style="font-size:3rem;">📭</div>
            <p style="color:#8892a4;">No submissions found for this session.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    evaluated   = [s for s in subs if s["score"] is not None]
    total_score = sum(s["score"] for s in evaluated)
    total_max   = sum(s["max_marks"] for s in subs)
    pct         = (total_score / total_max * 100) if evaluated and total_max else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f'<div class="stat-card"><span class="stat-val">{len(subs)}</span><span class="stat-label">Answered</span></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="stat-card"><span class="stat-val">{len(evaluated)}</span><span class="stat-label">Evaluated</span></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="stat-card"><span class="stat-val">{total_score:.1f}/{total_max}</span><span class="stat-label">Score</span></div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="stat-card"><span class="stat-val">{pct:.1f}%</span><span class="stat-label">Percentage</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    for i, sub in enumerate(subs, 1):
        if sub["score"] is not None:
            score_label = f"{sub['score']:.1f} / {sub['max_marks']}"
        else:
            score_label = "Pending"
        with st.expander(f"Question {i}  |  Score: {score_label}"):
            st.markdown(f"**Question:**")
            st.markdown(f"> {sub['question_text']}")
            st.markdown("**Your Answer:**")
            if sub.get("answer_type") == "image" and sub.get("answer_image"):
                st.markdown("<span style='color:#00d4aa; font-size:0.85rem;'>📷 Handwritten Answer</span>", unsafe_allow_html=True)
                import io
                from PIL import Image
                try:
                    img = Image.open(io.BytesIO(sub["answer_image"]))
                    st.image(img, caption="Your handwritten answer", width=500)
                except Exception:
                    st.warning("Could not display image.")
            else:
                st.markdown(f"> {sub.get('answer_text', 'No answer recorded')}")
            if sub.get("feedback"):
                st.markdown(f"""
                <div class="feedback-box">
                    <div class="fb-label">AI Feedback</div>
                    {sub["feedback"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.caption("Evaluation pending — check back after admin triggers evaluation.")


# ══════════════════════════════════════════════════════════════════
#  RANKINGS
# ══════════════════════════════════════════════════════════════════
def show_rankings():
    st.markdown("""
    <div class="hero-banner">
        <div class="badge">Leaderboard</div>
        <h1>🏆 Rankings</h1>
        <div class="subtitle">Top performers of the session</div>
    </div>
    """, unsafe_allow_html=True)

    sessions = db.get_all_sessions()
    if not sessions:
        st.info("No sessions available.")
        return

    sel = st.selectbox("Select Session", [f"{s['id']} — {s['title']}" for s in sessions])
    sid = int(sel.split("—")[0].strip())

    rankings = db.get_rankings(sid)
    if not rankings:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0f1729,#162040); border:1px solid rgba(240,192,96,0.18);
             border-radius:12px; padding:2rem; text-align:center;">
            <div style="font-size:3rem;">📊</div>
            <p style="color:#8892a4;">No evaluated submissions yet for this session.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    medals = ["🥇", "🥈", "🥉"]
    st.markdown("<br>", unsafe_allow_html=True)

    for rank, row in enumerate(rankings, 1):
        medal     = medals[rank - 1] if rank <= 3 else f"#{rank}"
        cls       = f"rank-{rank}" if rank <= 3 else ""
        score_val = f"{row['total_score']:.1f} / {row['total_max']}" if row["total_score"] is not None else "—"
        pct       = (row["total_score"] / row["total_max"] * 100) if row["total_score"] and row["total_max"] else 0
        pct_str   = f"{pct:.1f}"
        bar_w     = int(pct)

        st.markdown(f"""
        <div class="rank-card {cls}">
            <div class="rank-medal">{medal}</div>
            <div style="flex:1">
                <div class="rank-name">{row["name"]}</div>
                <div class="rank-email">{row["email"]}</div>
                <div class="score-bar-bg">
                    <div class="score-bar-fill" style="width:{bar_w}%"></div>
                </div>
            </div>
            <div class="rank-score">
                <div class="score-val">{score_val}</div>
                <div class="score-pct">{pct_str}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ══════════════════════════════════════════════════════════════════
def show_admin_panel():
    st.markdown("""
    <div class="hero-banner">
        <div class="badge">Admin Only</div>
        <h1>Admin Panel</h1>
        <div class="subtitle">Manage sessions, questions, and evaluations</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋  Sessions", "❓  Questions", "🤖  Evaluate", "📊  Submissions"])

    with tab1:
        st.markdown('<div class="section-title">Create New Session</div>', unsafe_allow_html=True)
        with st.form("create_session"):
            title = st.text_input("Session Title", placeholder="e.g. EMRS ESSE Mock Test 1")
            desc  = st.text_area("Description (optional)", height=80)
            if st.form_submit_button("Create & Activate Session", type="primary"):
                if title:
                    db.create_session(title, desc)
                    st.success(f"Session '{title}' created and activated!")
                    st.rerun()
                else:
                    st.error("Session title is required.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">All Sessions</div>', unsafe_allow_html=True)
        for s in db.get_all_sessions():
            badge_cls  = "badge-active" if s["is_active"] else "badge-closed"
            badge_text = "Active" if s["is_active"] else "Closed"
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                <div class="admin-stat">
                    <div>
                        <div class="as-title">{s["title"]}</div>
                        <small style="color:#8892a4;">{s.get("description") or "No description"}</small>
                    </div>
                    <span class="as-badge {badge_cls}">{badge_text}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if s["is_active"]:
                    if st.button("Close", key=f"close_{s['id']}"):
                        db.close_session(s["id"])
                        st.rerun()

    with tab2:
        session = db.get_active_session()
        if not session:
            st.warning("No active session. Create one in the Sessions tab first.")
        else:
            st.markdown(f"""
            <div style="background:rgba(0,212,170,0.08); border:1px solid rgba(0,212,170,0.2);
                 border-radius:10px; padding:0.8rem 1.2rem; margin-bottom:1.2rem; color:#a0f0e0;">
                Active session: <b style="color:#00d4aa;">{session["title"]}</b>
            </div>
            """, unsafe_allow_html=True)

            with st.form("add_question"):
                qtext = st.text_area("Question Text", height=120, placeholder="Enter descriptive question...")
                col1, col2 = st.columns(2)
                marks = col1.number_input("Marks", min_value=1, max_value=20, value=4)
                hint  = col2.text_input("Hint (optional)")
                if st.form_submit_button("Add Question", type="primary"):
                    if qtext.strip():
                        db.add_question(session["id"], qtext.strip(), marks, hint)
                        st.success("Question added!")
                        st.rerun()
                    else:
                        st.error("Question text cannot be empty.")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">Current Questions</div>', unsafe_allow_html=True)
            questions = db.get_questions_for_session(session["id"])
            if not questions:
                st.caption("No questions yet.")
            for i, q in enumerate(questions, 1):
                preview = q["question_text"][:70] + "..." if len(q["question_text"]) > 70 else q["question_text"]
                with st.expander(f"Q{i}: {preview}  [{q['marks']} marks]"):
                    st.write(q["question_text"])
                    if q.get("hint"):
                        st.caption(f"Hint: {q['hint']}")
                    if st.button("Delete", key=f"del_{q['id']}"):
                        db.delete_question(q["id"])
                        st.rerun()

    with tab3:
        sessions = db.get_all_sessions()
        if not sessions:
            st.info("No sessions found.")
        else:
            sel     = st.selectbox("Select Session", [f"{s['id']} — {s['title']}" for s in sessions])
            sid     = int(sel.split("—")[0].strip())
            pending = db.get_unevaluated_submissions(sid)
            st.metric("Pending Evaluations", len(pending))

            if not GEMINI_API_KEY:
                st.error("GEMINI_API_KEY not set in .env file!")
            elif pending:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🤖  Evaluate All Pending Answers", type="primary", use_container_width=True):
                    progress = st.progress(0, "Starting AI evaluation...")
                    for i, sub in enumerate(pending):
                        pct_val = (i + 1) / len(pending)
                        progress.progress(pct_val, f"Evaluating {i+1}/{len(pending)} — {sub['student_name']}")
                        if sub.get("answer_type") == "image" and sub.get("answer_image"):
                            result = evaluator.evaluate_image_answer(sub["question_text"], sub["answer_image"], sub["max_marks"])
                        else:
                            result = evaluator.evaluate_answer(sub["question_text"], sub.get("answer_text", ""), sub["max_marks"])
                        db.save_evaluation(sub["id"], result["score"], result["feedback"])
                        time.sleep(0.5)
                    progress.empty()
                    st.success(f"Successfully evaluated {len(pending)} answers!")
                    st.rerun()
            else:
                st.success("All submitted answers are already evaluated!")

    with tab4:
        sessions = db.get_all_sessions()
        if not sessions:
            st.info("No sessions found.")
        else:
            sel  = st.selectbox("Select Session", [f"{s['id']} — {s['title']}" for s in sessions], key="view_sess")
            sid  = int(sel.split("—")[0].strip())
            subs = db.get_all_submissions_for_session(sid)

            if not subs:
                st.info("No submissions for this session.")
            else:
                import pandas as pd
                df = pd.DataFrame(subs)[["student_name", "student_email", "question_text", "answer_text", "score", "max_marks", "feedback", "submitted_at"]]
                df.columns = ["Name", "Email", "Question", "Answer", "Score", "Max", "Feedback", "Submitted At"]
                st.dataframe(df, use_container_width=True, height=400)
                csv = df.to_csv(index=False).encode()
                st.download_button("Download CSV", csv, "submissions.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════════════════════════════
def main():
    user = st.session_state.user
    if user is None:
        show_login_page()
        return

    page = show_sidebar()

    if "Exam" in page:
        show_exam_page()
    elif "Rankings" in page:
        show_rankings()
    elif "Results" in page:
        show_my_results()
    elif "Admin" in page:
        if user["role"] == "admin":
            show_admin_panel()
        else:
            st.error("Access denied. Admins only.")

if __name__ == "__main__":
    main()