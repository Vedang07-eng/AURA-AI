import os
import json
import hashlib
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st

# ----------------------------
# Load Environment Variables
# ----------------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY not found in .env file")
    st.stop()

client = genai.Client(api_key=api_key)

# ----------------------------
# Accounts + Per-User Chat Storage
# ----------------------------
USERS_FILE = "users.json"
CHAT_DIR = "chat_histories"
os.makedirs(CHAT_DIR, exist_ok=True)

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@gmail\.com$")


def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def user_file_path(email):
    safe = "".join(c for c in email if c.isalnum() or c in ("_", "-", ".")).lower()
    return os.path.join(CHAT_DIR, f"{safe}.json")


def load_chat_data(email):
    path = user_file_path(email)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"current": [], "sessions": []}
    return {"current": [], "sessions": []}


def save_chat_data(email, data):
    path = user_file_path(email)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def make_title(messages):
    for m in messages:
        if m["role"] == "user":
            text = m["content"].strip()
            return (text[:35] + "…") if len(text) > 35 else text
    return "New conversation"


# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="AURA AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide the sidebar to focus on the main UI dashboard
)

# ----------------------------
# CSS — Light, SaaS-style theme
# ----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp { background: #FFFFFF; }
.block-container { max-width: 1200px; padding-top: 0rem; padding-bottom: 2rem; }
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stMarkdownContainer"] { width: 100%; }

.announce-bar {
    background: linear-gradient(90deg, #4F46E5, #7C3AED);
    color: white; text-align: center; font-weight: 600; font-size: 1rem;
    padding: 12px 12px; width: 100vw; position: relative;
    left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw;
    margin-top: -1rem; margin-bottom: 1rem; letter-spacing: 0.2px;
}
.navbar {
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
    gap: 16px; padding: 16px 0 18px 0; border-bottom: 1px solid #EEF0F5; margin-bottom: 0.5rem;
}
.nav-brand {
    display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.5rem;
    color: #16182B; text-decoration: none; flex-shrink: 0;
}
.nav-brand .logo-circle {
    width: 42px; height: 42px; border-radius: 12px;
    background: linear-gradient(135deg, #6366F1, #A855F7);
    display: flex; align-items: center; justify-content: center; font-size: 20px;
    box-shadow: 0 4px 12px rgba(99,102,241,0.35); flex-shrink: 0;
}
.nav-links { display: flex; flex-wrap: wrap; align-items: center; gap: 30px; margin-left: auto; }
.nav-links a { color: #3A3D52; text-decoration: none; font-weight: 600; font-size: 1.05rem; transition: color 0.15s ease; white-space: nowrap; }
.nav-links a:hover { color: #6366F1; }
.nav-cta {
    background: linear-gradient(135deg, #6366F1, #8B5CF6); color: white !important;
    padding: 10px 22px; border-radius: 10px; font-weight: 700; font-size: 1rem;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3); white-space: nowrap;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 8px; background: #EEF2FF; color: #4F46E5;
    font-weight: 600; font-size: 0.95rem; padding: 8px 18px; border-radius: 999px; margin: 2.2rem 0 1.4rem 0; border: 1px solid #E0E7FF;
}
.hero-title { font-size: 3.6rem; font-weight: 900; line-height: 1.15; color: #14162B; letter-spacing: -1px; margin-bottom: 0.3rem; }
.hero-title .accent { background: linear-gradient(135deg, #6366F1, #A855F7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-sub { font-size: 1.28rem; color: #666B85; max-width: 680px; line-height: 1.65; margin: 1.2rem 0 2rem 0; }
.quote-block { background: linear-gradient(135deg, #EEF2FF 0%, #F5F0FF 100%); border: 1px solid #E5E0FF; border-radius: 22px; padding: 3rem 2.5rem; text-align: center; margin: 2.5rem 0 3rem 0; }
.quote-mark { font-size: 3.4rem; color: #A5B4FC; font-weight: 900; line-height: 0; }
.quote-text { font-size: 2.25rem; font-weight: 800; color: #23253B; line-height: 1.4; max-width: 820px; margin: 0.8rem auto 1.2rem auto; letter-spacing: -0.5px; }
.feature-row { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 22px; }
.feature-icon { min-width: 42px; height: 42px; border-radius: 12px; background: #EEF2FF; display: flex; align-items: center; justify-content: center; font-size: 19px; }
.feature-text h4 { margin: 0 0 3px 0; font-size: 1.15rem; color: #16182B; font-weight: 700; }
.feature-text p { margin: 0; color: #6B7280; font-size: 1rem; line-height: 1.5; }
.section-title { display: block; width: 100%; box-sizing: border-box; font-size: 2.4rem; font-weight: 800; color: #16182B; text-align: center !important; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.section-sub { display: block; width: 100%; box-sizing: border-box; text-align: center !important; color: #6B7280; font-size: 1.1rem; max-width: 640px; margin: 0 auto 2.2rem auto; }
.about-card { background: #FFFFFF; border: 1px solid #EEF0F5; border-radius: 18px; padding: 24px; box-shadow: 0 2px 10px rgba(16,24,40,0.04); height: 100%; transition: transform 0.15s ease, box-shadow 0.15s ease; display: flex; flex-direction: column; align-items: flex-start; text-align: left; }
.about-card:hover { transform: translateY(-3px); box-shadow: 0 10px 22px rgba(16,24,40,0.08); }
.about-card .icon { font-size: 28px; margin-bottom: 12px; display: block; }
.about-card h3 { font-size: 1.15rem; font-weight: 700; color: #16182B; margin: 0 0 8px 0; }
.about-card p { font-size: 0.98rem; color: #6B7280; margin: 0; line-height: 1.55; }
.author-card { background: linear-gradient(135deg, #16182B, #2A2D4A); border-radius: 22px; padding: 2.5rem; text-align: center; color: white; margin: 1.5rem 0 3rem 0; }
.author-avatar { width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg, #6366F1, #A855F7); display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 800; margin: 0 auto 14px auto; }
.author-card h3 { margin: 0 0 4px 0; font-size: 1.3rem; font-weight: 800; }
.author-card p { color: #B8BAD0; margin: 0; font-size: 0.95rem; }

/* Dashboard Component Shells */
.chat-wrapper { background: #F8F9FC; border: 1px solid #E6EAF0; border-radius: 22px; padding: 1.5rem; margin-bottom: 1.5rem; }
.history-wrapper { background: #FFFFFF; border: 1px solid #EEF0F5; border-radius: 22px; padding: 1.5rem; box-shadow: 0 4px 14px rgba(16,24,40,0.03); height: 100%; min-height: 500px; }
.stChatMessage { background: #FFFFFF; border: 1px solid #E2E5EE; border-radius: 16px; padding: 10px 14px; box-shadow: 0 2px 8px rgba(16,24,40,0.05); font-size: 1.05rem; margin-bottom: 4px; }
[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) { background: #EEF2FF; border-color: #C7D2FE; }

/* Login Panel Styling Elements */
.auth-title { font-size: 2rem; font-weight: 800; text-align: center; color: #16182B; margin-bottom: 0.5rem; }
.auth-sub { text-align: center; color: #6B7280; font-size: 1rem; margin-bottom: 2rem; }
.auth-note { text-align: center; color: #9CA3AF; font-size: 0.85rem; margin-top: 1.5rem; }
.auth-logo { display: flex; justify-content: center; margin-bottom: 1rem; }
.auth-logo .logo-circle { width: 50px; height: 50px; border-radius: 14px; background: linear-gradient(135deg, #6366F1, #A855F7); display: flex; align-items: center; justify-content: center; font-size: 24px; color: white; box-shadow: 0 4px 12px rgba(99,102,241,0.35); }

/* Custom Main Page Buttons Layout Override */
.stButton > button { background: #FFFFFF; color: #16182B; border: 1px solid #E6EAF0; border-radius: 10px; font-weight: 500; text-align: left; justify-content: flex-start; box-shadow: none; padding: 10px 12px; }
.stButton > button:hover { background: #EEF2FF; border-color: #C7D2FE; color: #16182B; }
.action-btn-primary > div > button { background: linear-gradient(135deg, #6366F1, #8B5CF6); color: white !important; border: none; justify-content: center; font-weight: 700; text-align: center; box-shadow: 0 4px 12px rgba(99,102,241,0.3); }
.action-btn-primary > div > button:hover { opacity: 0.95; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Auth state init
# ----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "active_session_idx" not in st.session_state:
    st.session_state.active_session_idx = None

if st.session_state.user is None:
    st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="auth-logo"><div class="logo-circle">✨</div></div>
    <div class="auth-title">Welcome to AURA AI</div>
    <div class="auth-sub">Sign in with your Gmail address — your chats stay private to your account.</div>
    """, unsafe_allow_html=True)

    left, mid, right = st.columns([1, 2, 1])

    with mid:
        login_tab, signup_tab = st.tabs(["🔑 Login", "🆕 Sign Up"])

        with login_tab:
            with st.form("login_form"):
                login_email = st.text_input("Gmail Address", placeholder="you@gmail.com")
                login_pass = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log In", use_container_width=True)

                if submitted:
                    users = load_users()
                    email = login_email.strip().lower()
                    if email in users and users[email]["password"] == hash_password(login_pass):
                        st.session_state.user = email
                        data = load_chat_data(email)
                        st.session_state.messages = data.get("current", [])
                        st.session_state.history = data.get("sessions", [])
                        st.session_state.active_session_idx = None
                        st.rerun()
                    else:
                        st.error("❌ Invalid Gmail address or password.")

        with signup_tab:
            with st.form("signup_form"):
                new_email = st.text_input("Gmail Address", placeholder="you@gmail.com")
                new_pass = st.text_input("Create a password", type="password")
                new_pass_confirm = st.text_input("Confirm password", type="password")
                signed_up = st.form_submit_button("Create Account", use_container_width=True)

                if signed_up:
                    email = new_email.strip().lower()
                    users = load_users()
                    if not EMAIL_RE.match(email):
                        st.error("❌ Please enter a valid Gmail address (e.g. name@gmail.com).")
                    elif not new_pass:
                        st.error("❌ Please choose a password.")
                    elif email in users:
                        st.error("❌ An account with that Gmail address already exists.")
                    elif new_pass != new_pass_confirm:
                        st.error("❌ Passwords do not match.")
                    else:
                        users[email] = {"password": hash_password(new_pass)}
                        save_users(users)
                        st.session_state.user = email
                        st.session_state.messages = []
                        st.session_state.history = []
                        st.session_state.active_session_idx = None
                        save_chat_data(email, {"current": [], "sessions": []})
                        st.success("✅ Account created! Redirecting...")
                        st.rerun()
    st.stop()

# ============================================================
# MAIN APP ENGINE
# ============================================================
user_email = st.session_state.user

if "messages" not in st.session_state:
    data = load_chat_data(user_email)
    st.session_state.messages = data.get("current", [])
    st.session_state.history = data.get("sessions", [])

# ----------------------------
# Interface Markup Header Sections
# ----------------------------
st.markdown('<div class="announce-bar">✨ Meet AURA AI — Your Personal Assistant Powered by Gemini. Try it free now!</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="navbar">
    <a href="#top" class="nav-brand">
        <div class="logo-circle">✨</div>
        AURA AI
    </a>
    <div style="font-weight: 600; color: #4F46E5; margin-left: 20px;">👤 ID: {user_email}</div>
    <div class="nav-links">
        <a href="#about">About</a>
        <a href="#resources">Resources</a>
        <a href="#author">Author</a>
        <a href="#chat-section" class="nav-cta">Go to Chat Console</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<a id="top"></a>', unsafe_allow_html=True)
st.markdown('<span class="hero-badge">🟢 Online &nbsp;·&nbsp; Powered by Gemini 2.5 Flash</span>', unsafe_allow_html=True)

st.markdown("""
<div class="hero-title">Smarter Conversations,<br><span class="accent">Powered by AI.</span></div>
<p class="hero-sub">AURA AI helps you think faster, write better, and solve problems instantly — a personal AI assistant available 24/7, ready whenever you are.</p>
""", unsafe_allow_html=True)

st.markdown('<div class="quote-block"><div class="quote-mark">"</div><div class="quote-text">The future belongs to those who learn more, ask more, and never stop being curious.</div><div class="quote-mark">"</div></div>', unsafe_allow_html=True)

# Product Info Elements
feat_col1, feat_col2 = st.columns(2)
with feat_col1:
    st.markdown('<div class="feature-row"><div class="feature-icon">⚡</div><div class="feature-text"><h4>Instant Responses</h4><p>Get fast, accurate answers in real time — no waiting around.</p></div></div><div class="feature-row"><div class="feature-icon">🧠</div><div class="feature-text"><h4>Context Aware</h4><p>AURA remembers your conversation and responds intelligently.</p></div></div>', unsafe_allow_html=True)
with feat_col2:
    st.markdown('<div class="feature-row"><div class="feature-icon">🔒</div><div class="feature-text"><h4>Secure & Private</h4><p>Your conversations are handled securely, every single time.</p></div></div><div class="feature-row"><div class="feature-icon">🌍</div><div class="feature-text"><h4>Always Available</h4><p>24/7 AI support — whenever inspiration or a question strikes.</p></div></div>', unsafe_allow_html=True)

st.divider()
st.markdown('<a id="about"></a><div class="section-title">About AURA AI</div>', unsafe_allow_html=True)
about_col1, about_col2, about_col3 = st.columns(3)
with about_col1: st.markdown('<div class="about-card"><span class="icon">💬</span><h3>Natural Conversations</h3><p>Chat naturally with an AI that understands context and nuance.</p></div>', unsafe_allow_html=True)
with about_col2: st.markdown('<div class="about-card"><span class="icon">🎯</span><h3>Purpose Built</h3><p>Designed for productivity — writing, research, brainstorming and more.</p></div>', unsafe_allow_html=True)
with about_col3: st.markdown('<div class="about-card"><span class="icon">🚀</span><h3>Built on Gemini</h3><p>Powered by Google\'s Gemini 2.5 Flash for fast, quality responses.</p></div>', unsafe_allow_html=True)

st.divider()
st.markdown('<a id="resources"></a><div class="section-title">Resources</div>', unsafe_allow_html=True)
res_col1, res_col2, res_col3 = st.columns(3)
with res_col1: st.markdown('<div class="about-card"><span class="icon">📘</span><h3>Getting Started</h3><p>Learn how to make the most of your conversations with AURA.</p></div>', unsafe_allow_html=True)
with res_col2: st.markdown('<div class="about-card"><span class="icon">🛠️</span><h3>Tips & Tricks</h3><p>Prompting techniques to get sharper, more useful answers.</p></div>', unsafe_allow_html=True)
with res_col3: st.markdown('<div class="about-card"><span class="icon">❓</span><h3>FAQ</h3><p>Answers to common questions about AURA AI and how it works.</p></div>', unsafe_allow_html=True)

st.divider()
st.markdown('<a id="author"></a><div class="section-title">Meet the Author</div><div class="author-card"><div class="author-avatar">VD</div><h3>Vedang Dhuri</h3><p>Creator & Developer of AURA AI</p></div>', unsafe_allow_html=True)

st.divider()

# ============================================================
# NEW 2-COLUMN MAIN DASHBOARD INTERFACE
# ============================================================
st.markdown('<a id="chat-section"></a><div class="section-title">AURA AI Workspace Console</div>', unsafe_allow_html=True)

workspace_chat_col, workspace_history_col = st.columns([2.3, 1])

# ----------------------------
# LEFT COLUMN: Active Playground Chat Sandbox
# ----------------------------
with workspace_chat_col:
    st.markdown('<p style="font-weight:700; color:#16182B; font-size:1.2rem; margin-bottom:0.5rem;">💬 Active Chat Sandbox</p>', unsafe_allow_html=True)
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown('<p style="text-align:center; color:#9CA3AF; margin: 2rem 0;">👋 Workspace is empty. Ask AURA AI anything below to begin.</p>', unsafe_allow_html=True)
    else:
        for message in st.session_state.messages:
            avatar = "🧑‍💻" if message["role"] == "user" else "✨"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
                
    st.markdown('</div>', unsafe_allow_html=True)
    prompt = st.chat_input("Ask AURA AI anything...")

# ----------------------------
# RIGHT COLUMN: Always-Visible Chat History Panel
# ----------------------------
with workspace_history_col:
    st.markdown('<p style="font-weight:700; color:#16182B; font-size:1.2rem; margin-bottom:0.5rem;">🕓 Chat History Panel</p>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="history-wrapper">', unsafe_allow_html=True)
        
        # New Chat Control Button
        st.markdown('<div class="action-btn-primary">', unsafe_allow_html=True)
        if st.button("➕ Start New Chat", key="dashboard_new_chat", use_container_width=True):
            if st.session_state.messages:
                match_found = False
                for h in st.session_state.history:
                    if h["messages"] == st.session_state.messages:
                        match_found = True
                        break
                if not match_found:
                    st.session_state.history.insert(0, {
                        "title": make_title(st.session_state.messages),
                        "messages": list(st.session_state.messages)
                    })
            st.session_state.messages = []
            st.session_state.active_session_idx = None
            save_chat_data(user_email, {"current": [], "sessions": st.session_state.history})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)

        # Loop through data nodes
        if not st.session_state.history:
            st.markdown('<p style="color:#9CA3AF; font-size:0.95rem; text-align:center; margin-top:2rem;">No past chats recorded yet.</p>', unsafe_allow_html=True)
        else:
            for i, session in enumerate(st.session_state.history):
                col_load, col_del = st.columns([4, 1])
                with col_load:
                    icon = "✨" if st.session_state.active_session_idx == i else "💬"
                    if st.button(f"{icon} {session['title']}", key=f"dash_load_{i}", use_container_width=True):
                        st.session_state.messages = list(session["messages"])
                        st.session_state.active_session_idx = i
                        save_chat_data(user_email, {"current": st.session_state.messages, "sessions": st.session_state.history})
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"dash_del_{i}", help="Delete permanently"):
                        if st.session_state.active_session_idx == i:
                            st.session_state.messages = []
                            st.session_state.active_session_idx = None
                        elif st.session_state.active_session_idx is not None and st.session_state.active_session_idx > i:
                            st.session_state.active_session_idx -= 1
                            
                        del st.session_state.history[i]
                        save_chat_data(user_email, {"current": st.session_state.messages, "sessions": st.session_state.history})
                        st.rerun()

            st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
            if st.button("🧹 Clear All Histories", key="dash_clear_all", use_container_width=True):
                st.session_state.history = []
                st.session_state.messages = []
                st.session_state.active_session_idx = None
                save_chat_data(user_email, {"current": [], "sessions": []})
                st.rerun()

        st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
        st.divider()
        if st.button("🚪 Log Out", key="dash_logout", use_container_width=True):
            save_chat_data(user_email, {"current": st.session_state.messages, "sessions": st.session_state.history})
            st.session_state.user = None
            st.session_state.messages = []
            st.session_state.history = []
            st.session_state.active_session_idx = None
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# Prompt Execution Lifecycle Engine
# ----------------------------
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Re-verify workspace execution column layout context
    with workspace_chat_col:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        api_contents = []
        for msg in st.session_state.messages:
            api_contents.append(
                types.Content(
                    role="user" if msg["role"] == "user" else "model",
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        with st.chat_message("assistant", avatar="✨"):
            placeholder = st.empty()
            full_response = ""

            try:
                with st.spinner("AURA is thinking..."):
                    response_stream = client.models.generate_content_stream(
                        model="gemini-2.5-flash",
                        contents=api_contents
                    )
                    
                    for chunk in response_stream:
                        if chunk.text:
                            full_response += chunk.text
                            placeholder.markdown(full_response + "▌")
                    
                    placeholder.markdown(full_response)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })

                # History Pipeline Auto-Injector
                current_title = make_title(st.session_state.messages)
                
                if st.session_state.active_session_idx is not None:
                    st.session_state.history[st.session_state.active_session_idx]["messages"] = list(st.session_state.messages)
                    st.session_state.history[st.session_state.active_session_idx]["title"] = current_title
                else:
                    st.session_state.history.insert(0, {
                        "title": current_title,
                        "messages": list(st.session_state.messages)
                    })
                    st.session_state.active_session_idx = 0

                save_chat_data(user_email, {
                    "current": st.session_state.messages,
                    "sessions": st.session_state.history
                })
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")

# ----------------------------
# Footer Section
# ----------------------------
st.markdown("""
<div class="footer-dark">
    <div style="display:flex; flex-wrap:wrap; gap:2.5rem; justify-content:space-between;">
        <div style="min-width:200px;">
            <div class="footer-brand">✨ AURA AI</div>
            <p style="color:#9A9CBB; font-size:0.88rem; max-width:220px;">Your personal AI assistant, built for smarter conversations.</p>
        </div>
        <div class="footer-col">
            <h4>Product</h4>
            <a href="#top">Home</a>
            <a href="#chat-section">Chat</a>
        </div>
    </div>
    <div class="footer-bottom">
        Made with <span class="heart">❤️</span> by Vedang Dhuri · © 2026 AURA AI
    </div>
</div>
""", unsafe_allow_html=True)
