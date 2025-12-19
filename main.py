import streamlit as st
from openai import OpenAI

# --- 1. SETTINGS & CLOAKING ---
st.set_page_config(page_title="Kairo Pro", page_icon="⚡", layout="wide")

# Custom CSS to make it look like a real SaaS website
st.markdown("""
    <style>
    /* Hide Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Hero Section Styling */
    .hero-container {
        padding: 100px 0px;
        text-align: center;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        border-radius: 20px;
        margin-bottom: 50px;
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: 20px;
        background: -webkit-linear-gradient(#fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .feature-card {
        padding: 30px;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 15px;
        text-align: center;
        transition: 0.3s;
    }
    .feature-card:hover {
        border-color: #38bdf8;
        transform: translateY(-5px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PAGE NAVIGATION ---
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- 3. HOMEPAGE LAYOUT ---
if st.session_state.page == "home":
    # HERO SECTION
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">KAIRO PRO</h1>
            <p style="font-size: 1.5rem; color: #94a3b8;">The ultra-fast AI terminal powered by Grok 4.1</p>
        </div>
    """, unsafe_allow_html=True)

    # BUTTONS IN THE CENTER
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🚀 ENTER TERMINAL", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()

    st.divider()

    # FEATURES GRID
    st.subheader("Why choose Kairo?")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown('<div class="feature-card"><h3>🧠 Grok Engine</h3><p>Using xAI\'s latest models for unfiltered intelligence.</p></div>', unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="feature-card"><h3>📁 File Insight</h3><p>Upload PDFs or Images and chat with your data instantly.</p></div>', unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="feature-card"><h3>🔒 Zero Trace</h3><p>Private sessions that leave no footprint on your device.</p></div>', unsafe_allow_html=True)

# --- 4. CHAT TERMINAL (The actual app) ---
elif st.session_state.page == "chat":
    # Back button in sidebar
    if st.sidebar.button("⬅ Back to Home"):
        st.session_state.page = "home"
        st.rerun()
    
    st.title("🤖 Kairo Terminal")
    st.info("Currently using Grok-2 engine.")
    
    # [Insert your existing chat and file upload logic here]
    if prompt := st.chat_input("Message Kairo..."):
        with st.chat_message("user"):
            st.write(prompt)
