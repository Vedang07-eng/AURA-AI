import os
import json
from dotenv import load_dotenv
from google import genai
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
# Persistent Chat History (saved to disk)
# ----------------------------
HISTORY_FILE = "chat_data.json"

def load_data():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"current": [], "sessions": []}
    return {"current": [], "sessions": []}

def save_data(data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def make_title(messages):
    for m in messages:
        if m["role"] == "user":
            text = m["content"].strip()
            return (text[:40] + "…") if len(text) > 40 else text
    return "New conversation"

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="AURA AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# CSS — Light, SaaS-style theme
# ----------------------------
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #FFFFFF;
}

.block-container {
    max-width: 1100px;
    padding-top: 0rem;
    padding-bottom: 2rem;
}

#MainMenu, footer, header {visibility: hidden;}

/* Fix Streamlit markdown containers shrinking to content width,
   which breaks margin:auto centering on custom classes */
[data-testid="stMarkdownContainer"] {
    width: 100%;
}

/* ---------- Top announcement bar ---------- */
.announce-bar {
    background: linear-gradient(90deg, #4F46E5, #7C3AED);
    color: white;
    text-align: center;
    font-weight: 600;
    font-size: 1rem;
    padding: 12px 12px;
    width: 100vw;
    position: relative;
    left: 50%;
    right: 50%;
    margin-left: -50vw;
    margin-right: -50vw;
    margin-top: -1rem;
    margin-bottom: 1rem;
    letter-spacing: 0.2px;
}

/* ---------- Navbar ---------- */
.navbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px 0 18px 0;
    border-bottom: 1px solid #EEF0F5;
    margin-bottom: 0.5rem;
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 800;
    font-size: 1.5rem;
    color: #16182B;
    text-decoration: none;
    flex-shrink: 0;
}

.nav-brand .logo-circle {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg, #6366F1, #A855F7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 4px 12px rgba(99,102,241,0.35);
    flex-shrink: 0;
}

.nav-links {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 30px;
    margin-left: auto;
}

.nav-links a {
    color: #3A3D52;
    text-decoration: none;
    font-weight: 600;
    font-size: 1.05rem;
    transition: color 0.15s ease;
    white-space: nowrap;
}

.nav-links a:hover {
    color: #6366F1;
}

.nav-cta {
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    color: white !important;
    padding: 10px 22px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 1rem;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3);
    white-space: nowrap;
}

/* ---------- Hero ---------- */
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #EEF2FF;
    color: #4F46E5;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 8px 18px;
    border-radius: 999px;
    margin: 2.2rem 0 1.4rem 0;
    border: 1px solid #E0E7FF;
}

.hero-title {
    font-size: 3.6rem;
    font-weight: 900;
    line-height: 1.15;
    color: #14162B;
    letter-spacing: -1px;
    margin-bottom: 0.3rem;
}

.hero-title .accent {
    background: linear-gradient(135deg, #6366F1, #A855F7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-sub {
    font-size: 1.28rem;
    color: #666B85;
    max-width: 680px;
    line-height: 1.65;
    margin: 1.2rem 0 2rem 0;
}

/* ---------- Big motivational quote ---------- */
.quote-block {
    background: linear-gradient(135deg, #EEF2FF 0%, #F5F0FF 100%);
    border: 1px solid #E5E0FF;
    border-radius: 22px;
    padding: 3rem 2.5rem;
    text-align: center;
    margin: 2.5rem 0 3rem 0;
}

.quote-mark {
    font-size: 3.4rem;
    color: #A5B4FC;
    font-weight: 900;
    line-height: 0;
}

.quote-text {
    font-size: 2.25rem;
    font-weight: 800;
    color: #23253B;
    line-height: 1.4;
    max-width: 820px;
    margin: 0.8rem auto 1.2rem auto;
    letter-spacing: -0.5px;
}

.quote-author {
    color: #6366F1;
    font-weight: 700;
    font-size: 1.1rem;
}

/* ---------- Feature rows ---------- */
.feature-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 22px;
}

.feature-icon {
    min-width: 42px;
    height: 42px;
    border-radius: 12px;
    background: #EEF2FF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
}

.feature-text h4 {
    margin: 0 0 3px 0;
    font-size: 1.15rem;
    color: #16182B;
    font-weight: 700;
}

.feature-text p {
    margin: 0;
    color: #6B7280;
    font-size: 1rem;
    line-height: 1.5;
}

/* ---------- Section headers ---------- */
.section-title {
    display: block;
    width: 100%;
    box-sizing: border-box;
    font-size: 2.4rem;
    font-weight: 800;
    color: #16182B;
    text-align: center !important;
    letter-spacing: -0.5px;
    margin-bottom: 0.5rem;
}

.section-sub {
    display: block;
    width: 100%;
    box-sizing: border-box;
    text-align: right !important;
    color: #6B7280;
    font-size: 1.1rem;
    max-width: 640px;
    margin: 2rem auto 2.2rem auto;
}

/* ---------- About cards ---------- */
.about-card {
    background: #FFFFFF;
    border: 1px solid #EEF0F5;
    border-radius: 18px;
    padding: 24px;
    box-shadow: 0 2px 10px rgba(16,24,40,0.04);
    height: 100%;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.about-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 22px rgba(16,24,40,0.08);
}

.about-card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
}

.about-card .icon {
    font-size: 28px;
    margin-bottom: 12px;
    display: block;
}

.about-card h3 {
    font-size: 1.15rem;
    font-weight: 700;
    color: #16182B;
    margin: 0 0 8px 0;
}

.about-card p {
    font-size: 0.98rem;
    color: #6B7280;
    margin: 0;
    line-height: 1.55;
}

/* ---------- Author card ---------- */
.author-card {
    background: linear-gradient(135deg, #16182B, #2A2D4A);
    border-radius: 22px;
    padding: 2.5rem;
    text-align: center;
    color: white;
    margin: 1.5rem 0 3rem 0;
}

.author-avatar {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366F1, #A855F7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    font-weight: 800;
    margin: 0 auto 14px auto;
}

.author-card h3 {
    margin: 0 0 4px 0;
    font-size: 1.3rem;
    font-weight: 800;
}

.author-card p {
    color: #B8BAD0;
    margin: 0;
    font-size: 0.95rem;
}

/* ---------- Status pill ---------- */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #ECFDF5;
    color: #059669;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 6px 14px;
    border-radius: 999px;
    border: 1px solid #A7F3D0;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10B981;
}

/* ---------- Sidebar (Chat History) ---------- */
section[data-testid="stSidebar"] {
    background: #F8F9FC;
    border-right: 1px solid #E6EAF0;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

.sidebar-title {
    font-weight: 800;
    font-size: 1.1rem;
    color: #16182B;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

.history-empty {
    color: #9CA3AF;
    font-size: 0.9rem;
    padding: 8px 2px;
}

section[data-testid="stSidebar"] .stButton > button {
    background: #FFFFFF;
    color: #16182B;
    border: 1px solid #E6EAF0;
    box-shadow: none;
    font-weight: 500;
    text-align: left;
    justify-content: flex-start;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #EEF2FF;
    border-color: #C7D2FE;
    color: #16182B;
}

section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type > button {
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    color: white;
    border: none;
    justify-content: center;
}

/* ---------- Chat section ---------- */
.chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.chat-wrapper {
    background: #F8F9FC;
    border: 1px solid #E6EAF0;
    border-radius: 22px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.stChatMessage {
    background: #FFFFFF;
    border: 1px solid #E2E5EE;
    border-radius: 16px;
    padding: 10px 14px;
    box-shadow: 0 2px 8px rgba(16,24,40,0.05);
    font-size: 1.05rem;
    margin-bottom: 4px;
}

.stChatMessage p {
    font-size: 1.05rem;
    line-height: 1.6;
}

/* User message bubble */
[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
    background: #EEF2FF;
    border-color: #C7D2FE;
}

/* Chat input - make it stand out */
[data-testid="stChatInput"] {
    background: #FFFFFF;
    border: 2px solid #6366F1;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(99,102,241,0.18);
    padding: 4px 6px;
}

[data-testid="stChatInput"] textarea {
    font-size: 1.05rem !important;
}

[data-testid="stChatInputSubmitButton"] {
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    border-radius: 10px !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1rem;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3);
    transition: opacity 0.15s ease;
}

.stButton > button:hover {
    opacity: 0.9;
    color: white;
}

hr {
    border-color: #EEF0F5;
}

/* ---------- Footer ---------- */
.footer-dark {
    background: #14162B;
    color: #B8BAD0;
    border-radius: 22px;
    padding: 2.5rem 2.5rem 1.5rem 2.5rem;
    margin: 3rem -1rem 0 -1rem;
}

.footer-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    color: white;
    font-weight: 800;
    font-size: 1.15rem;
    margin-bottom: 8px;
}

.footer-col h4 {
    color: #FFFFFF;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin-bottom: 14px;
}

.footer-col p, .footer-col a {
    color: #9A9CBB;
    font-size: 0.9rem;
    text-decoration: none;
    display: block;
    margin-bottom: 10px;
}

.footer-col a:hover {
    color: white;
}

.footer-bottom {
    border-top: 1px solid #2A2D4A;
    margin-top: 1.5rem;
    padding-top: 1.2rem;
    text-align: center;
    color: #7A7CA0;
    font-size: 0.88rem;
}

.footer-bottom .heart {
    color: #F87171;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------
# Load persisted chat data into session state (runs once per session)
# ----------------------------

if "messages" not in st.session_state:
    _data = load_data()
    st.session_state.messages = _data.get("current", [])
    st.session_state.history = _data.get("sessions", [])

# ----------------------------
# Sidebar — Chat History
# ----------------------------

with st.sidebar:
    st.markdown('<div class="sidebar-title">🕓 &nbsp;Chat History</div>', unsafe_allow_html=True)

    if st.button("🆕  New Chat", use_container_width=True):
        if st.session_state.messages:
            st.session_state.history.insert(0, {
                "title": make_title(st.session_state.messages),
                "messages": st.session_state.messages
            })
        st.session_state.messages = []
        save_data({"current": [], "sessions": st.session_state.history})
        st.rerun()

    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown('<p class="history-empty">No past conversations yet. Start chatting and they\'ll show up here.</p>', unsafe_allow_html=True)
    else:
        for i, session in enumerate(st.session_state.history):
            if st.button(f"💬 {session['title']}", key=f"hist_{i}", use_container_width=True):
                if st.session_state.messages:
                    st.session_state.history.insert(0, {
                        "title": make_title(st.session_state.messages),
                        "messages": st.session_state.messages
                    })
                    del st.session_state.history[i + 1]
                else:
                    del st.session_state.history[i]
                st.session_state.messages = session["messages"]
                save_data({"current": st.session_state.messages, "sessions": st.session_state.history})
                st.rerun()

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
        if st.button("🗑️  Clear History", use_container_width=True):
            st.session_state.history = []
            save_data({"current": st.session_state.messages, "sessions": []})
            st.rerun()

# ----------------------------
# Announcement bar + Navbar
# ----------------------------

st.markdown('<div class="announce-bar">✨ Meet AURA AI — Your Personal Assistant Powered by Gemini. Try it free now!</div>', unsafe_allow_html=True)

st.markdown("""
<div class="navbar">
    <a href="#top" class="nav-brand">
        <div class="logo-circle">✨</div>
        AURA AI
    </a>
    <div class="nav-links">
        <a href="#about">About</a>
        <a href="#resources">Resources</a>
        <a href="#author">Author</a>
        <a href="#chat-section" class="nav-cta">Let's Start Chatting</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# Hero Section
# ----------------------------

st.markdown('<a id="top"></a>', unsafe_allow_html=True)

st.markdown('<span class="hero-badge">🟢 Online &nbsp;·&nbsp; Powered by Gemini 2.5 Flash</span>', unsafe_allow_html=True)

st.markdown("""
<div class="hero-title">Smarter Conversations,<br><span class="accent">Powered by AI.</span></div>
""", unsafe_allow_html=True)

st.markdown("""
<p class="hero-sub">AURA AI helps you think faster, write better, and solve problems instantly —
a personal AI assistant available 24/7, ready whenever you are.</p>
""", unsafe_allow_html=True)

hero_col1, hero_col2 = st.columns([1, 4])
with hero_col1:
    st.markdown('<a href="#chat-section" class="nav-cta" style="text-decoration:none; display:inline-block; padding:12px 26px; font-size:1rem;">🚀 Let\'s Start Chatting</a>', unsafe_allow_html=True)

st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)

# ----------------------------
# Big Motivational Quote
# ----------------------------

st.markdown("""
<div class="quote-block">
    <div class="quote-mark">"</div>
    <div class="quote-text">The future belongs to those who learn more, ask more, and never stop being curious.</div>
    <div class="quote-mark">"</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# Feature Highlights
# ----------------------------

feat_col1, feat_col2 = st.columns(2)

with feat_col1:
    st.markdown("""
    <div class="feature-row">
        <div class="feature-icon">⚡</div>
        <div class="feature-text">
            <h4>Instant Responses</h4>
            <p>Get fast, accurate answers in real time — no waiting around.</p>
        </div>
    </div>
    <div class="feature-row">
        <div class="feature-icon">🧠</div>
        <div class="feature-text">
            <h4>Context Aware</h4>
            <p>AURA remembers your conversation and responds intelligently.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with feat_col2:
    st.markdown("""
    <div class="feature-row">
        <div class="feature-icon">🔒</div>
        <div class="feature-text">
            <h4>Secure & Private</h4>
            <p>Your conversations are handled securely, every single time.</p>
        </div>
    </div>
    <div class="feature-row">
        <div class="feature-icon">🌍</div>
        <div class="feature-text">
            <h4>Always Available</h4>
            <p>24/7 AI support — whenever inspiration or a question strikes.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
st.divider()

# ----------------------------
# About Section
# ----------------------------

st.markdown('<a id="about"></a>', unsafe_allow_html=True)
st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">About AURA AI</div>', unsafe_allow_html=True)

about_col1, about_col2, about_col3 = st.columns(3)

with about_col1:
    st.markdown("""
    <div class="about-card">
        <span class="icon">💬</span>
        <h3>Natural Conversations</h3>
        <p>Chat naturally with an AI that understands context and nuance.</p>
    </div>
    """, unsafe_allow_html=True)

with about_col2:
    st.markdown("""
    <div class="about-card">
        <span class="icon">🎯</span>
        <h3>Purpose Built</h3>
        <p>Designed for productivity — writing, research, brainstorming and more.</p>
    </div>
    """, unsafe_allow_html=True)

with about_col3:
    st.markdown("""
    <div class="about-card">
        <span class="icon">🚀</span>
        <h3>Built on Gemini</h3>
        <p>Powered by Google's Gemini 2.5 Flash for fast, quality responses.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)
st.divider()

# ----------------------------
# Resources Section
# ----------------------------

st.markdown('<a id="resources"></a>', unsafe_allow_html=True)
st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Resources</div>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Everything you need to get the most out of AURA AI.</p>', unsafe_allow_html=True)

res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    st.markdown("""
    <div class="about-card">
        <span class="icon">📘</span>
        <h3>Getting Started</h3>
        <p>Learn how to make the most of your conversations with AURA.</p>
    </div>
    """, unsafe_allow_html=True)

with res_col2:
    st.markdown("""
    <div class="about-card">
        <span class="icon">🛠️</span>
        <h3>Tips & Tricks</h3>
        <p>Prompting techniques to get sharper, more useful answers.</p>
    </div>
    """, unsafe_allow_html=True)

with res_col3:
    st.markdown("""
    <div class="about-card">
        <span class="icon">❓</span>
        <h3>FAQ</h3>
        <p>Answers to common questions about AURA AI and how it works.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)
st.divider()

# ----------------------------
# Author Section
# ----------------------------

st.markdown('<a id="author"></a>', unsafe_allow_html=True)
st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Meet the Author</div>', unsafe_allow_html=True)

st.markdown("""
<div class="author-card">
    <div class="author-avatar">VD</div>
    <h3>Vedang Dhuri</h3>
    <p>Creator & Developer of AURA AI</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# Chat Section
# ----------------------------

st.markdown('<a id="chat-section"></a>', unsafe_allow_html=True)
st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Chat with AURA AI</div>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Ask anything — from quick questions to deep dives.</p>', unsafe_allow_html=True)

# ----------------------------
# Display Chat History
# ----------------------------

st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown(
        '<p style="text-align:center; color:#9CA3AF; margin-top:0.5rem; font-size:1.05rem;">👋 Start a conversation — ask AURA AI anything below.</p>',
        unsafe_allow_html=True
    )

for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ----------------------------
# Chat Input
# ----------------------------

prompt = st.chat_input("Ask AURA AI anything...")

st.markdown('</div>', unsafe_allow_html=True)

if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # Build conversation history
    conversation = []

    for msg in st.session_state.messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation.append(f"{role}: {msg['content']}")

    full_prompt = "\n".join(conversation)

    with st.chat_message("assistant", avatar="✨"):

        placeholder = st.empty()

        try:

            with st.spinner("AURA is thinking..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt
                )

            text = response.text if response.text else "No response received."

            streamed = ""

            for word in text.split():
                streamed += word + " "
                placeholder.markdown(streamed + "▌")

            placeholder.markdown(streamed)

            st.session_state.messages.append({
                "role": "assistant",
                "content": streamed
            })

            save_data({
                "current": st.session_state.messages,
                "sessions": st.session_state.history
            })

        except Exception as e:
            st.error(f"❌ Error: {e}")

# ----------------------------
# Footer
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
            <a href="#about">About</a>
        </div>
        <div class="footer-col">
            <h4>Resources</h4>
            <a href="#resources">Getting Started</a>
            <a href="#resources">FAQ</a>
            <a href="#resources">Tips & Tricks</a>
        </div>
        <div class="footer-col">
            <h4>Company</h4>
            <a href="#author">Author</a>
            <a href="#about">About Us</a>
        </div>
    </div>
    <div class="footer-bottom">
        Made with <span class="heart">♥</span> by <strong style="color:white;">Vedang Dhuri</strong> &nbsp;·&nbsp; Powered by Google Gemini
    </div>
</div>
""", unsafe_allow_html=True)