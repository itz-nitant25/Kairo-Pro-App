import streamlit as st
from openai import OpenAI
from supabase import create_client

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Kairo Pro", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp {background-color: #0b0f19;}
    .hero-text {text-align: center; padding: 60px 0; color: white;}
    .box {background: #161b22; padding: 2.5rem; border-radius: 15px; border: 1px solid #30363d; color: white;}
    .stButton>button {width: 100%; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECTIONS ---
try:
    client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Missing Secrets in Streamlit Cloud Settings.")
    st.stop()

# --- 3. SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. NAVIGATION LOGIC ---

# PAGE: LOGIN
if st.session_state.page == "home" and not st.session_state.logged_in:
    st.markdown("<div class='hero-text'><h1>KAIRO PRO</h1><p>The Ultra-Fast AI Terminal</p></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<div class='box'>", unsafe_allow_html=True)
        st.subheader("Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Enter Terminal", type="primary"):
            res = supabase.table("profiles").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.user_data = res.data[0]
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("Invalid Username or Password")
        
        st.divider()
        st.write("New to Kairo?")
        if st.button("Create a Kairo ID"):
            st.session_state.page = "signup"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# PAGE: SIGNUP
elif st.session_state.page == "signup":
    st.markdown("<div class='hero-text'><h1>GET YOUR KAIRO ID</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<div class='box'>", unsafe_allow_html=True)
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        conf_p = st.text_input("Confirm Password", type="password")
        
        if st.button("Register Account", type="primary"):
            if new_p != conf_p:
                st.error("Passwords do not match!")
            elif len(new_u) < 3:
                st.error("Username too short")
            else:
                try:
                    supabase.table("profiles").insert({"username": new_u, "password": new_p}).execute()
                    st.success("Account created! Returning to login...")
                    st.session_state.page = "home"
                    st.rerun()
                except:
                    st.error("Username already taken.")
        
        if st.button("Cancel"):
            st.session_state.page = "home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# PAGE: CHAT TERMINAL
elif st.session_state.logged_in:
    with st.sidebar:
        st.title("🤖 Kairo Pro")
        st.write(f"Logged in: **{st.session_state.user_data['username']}**")
        
        if st.button("➕ New Chat"):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.subheader("Chat History")
        history = supabase.table("chats").select("*").eq("user_id", st.session_state.user_data['id']).order("created_at", desc=True).limit(8).execute()
        for chat in history.data:
            label = chat['messages'][0]['content'][:20] + "..." if chat['messages'] else "Old Chat"
            if st.button(label, key=chat['id']):
                st.session_state.messages = chat['messages']
                st.rerun()

        st.divider()
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.page = "home"
            st.rerun()

    # Chat UI
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Command Kairo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model="grok-2-1212",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            supabase.table("chats").insert({
                "user_id": st.session_state.user_data['id'],
                "messages": st.session_state.messages
            }).execute()
