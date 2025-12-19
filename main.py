import streamlit as st
from openai import OpenAI
from supabase import create_client

# --- 1. PAGE CONFIG & STEALTH STYLING ---
st.set_page_config(page_title="Kairo Pro", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp {background-color: #0b0f19;}
    .hero-text {text-align: center; padding: 50px 0; color: white;}
    .login-box {background: #161b22; padding: 2rem; border-radius: 15px; border: 1px solid #30363d;}
    .sidebar-history-btn {margin-bottom: 5px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZE CLIENTS ---
try:
    client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Missing Secrets: XAI_API_KEY, SUPABASE_URL, or SUPABASE_KEY.")
    st.stop()

# --- 3. SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. NAVIGATION LOGIC ---

# PAGE: HOMEPAGE
if st.session_state.page == "home" and not st.session_state.logged_in:
    st.markdown("<div class='hero-text'><h1>KAIRO PRO</h1><p>Intelligence without limits. Powered by Grok.</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.subheader("Login to Terminal")
        user_in = st.text_input("Username")
        pass_in = st.text_input("Password", type="password")
        
        if st.button("Enter Kairo", use_container_width=True, type="primary"):
            res = supabase.table("profiles").select("*").eq("username", user_in).eq("password", pass_in).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.user_data = res.data[0]
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("Invalid Credentials")
        st.markdown("</div>", unsafe_allow_html=True)

# PAGE: CHAT TERMINAL
elif st.session_state.logged_in:
    with st.sidebar:
        st.title("🤖 Kairo Pro")
        st.write(f"Active: **{st.session_state.user_data['username']}**")
        
        # New Chat Button
        if st.button("➕ New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        # Load Past Chats from Supabase
        st.divider()
        st.subheader("📜 History")
        past_chats = supabase.table("chats").select("*").eq("user_id", st.session_state.user_data['id']).order("created_at", desc=True).limit(10).execute()
        
        for chat in past_chats.data:
            # Create a label from the first message
            label = chat['messages'][0]['content'][:25] + "..." if chat['messages'] else "Empty Chat"
            if st.button(label, key=chat['id'], use_container_width=True):
                st.session_state.messages = chat['messages']
                st.rerun()
        
        st.divider()
        uploaded_file = st.file_uploader("📎 Attach context", type=['txt', 'pdf', 'png', 'jpg'])
        
        if st.button("Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.page = "home"
            st.rerun()

    # Chat Interface
    st.title("Terminal")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Command Kairo..."):
        full_prompt = prompt
        if uploaded_file:
            full_prompt = f"[User uploaded {uploaded_file.name}]\n\n" + prompt

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(
                    model="grok-2-1212",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Save to Supabase
                supabase.table("chats").insert({
                    "user_id": st.session_state.user_data['id'],
                    "messages": st.session_state.messages
                }).execute()
            except Exception as e:
                st.error(f"Engine Error: {e}")
