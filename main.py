import streamlit as st
from openai import OpenAI
from supabase import create_client
import base64

# --- 1. PROFESSIONAL BRANDING (Hides Streamlit UI) ---
st.set_page_config(page_title="Kairo Pro", page_icon="⚡", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            #stDecoration {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
try:
    # xAI Grok Setup
    client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
    # Supabase Setup
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("⚠️ Setup incomplete. Check your Streamlit Secrets.")
    st.stop()

# --- 3. SESSION & LOGIN LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    with st.sidebar:
        st.title("👤 Kairo Account")
        user_in = st.text_input("Username")
        pass_in = st.text_input("Password", type="password")
        if st.button("Log In"):
            res = supabase.table("profiles").select("*").eq("username", user_in).eq("password", pass_in).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.user_id = res.data[0]["id"]
                st.session_state.username = res.data[0]["username"]
                st.rerun()
            else:
                st.error("Access Denied.")

# --- 4. MAIN INTERFACE ---
if not st.session_state.logged_in:
    st.header("Welcome to Kairo")
    st.info("Please sign in to access the private Grok terminal.")
    login()
else:
    # Sidebar: Model Selection & History
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.username}**")
        
        # Grok Options
        st.session_state.model = st.selectbox(
            "AI Engine", 
            ["grok-4.1-thinking", "grok-4.1", "grok-4-fast"],
            help="Thinking mode is best for complex logic."
        )
        
        # File Upload Option
        uploaded_file = st.file_uploader("📎 Upload a file to analyze", type=['txt', 'pdf', 'csv', 'png', 'jpg'])
        if uploaded_file:
            st.success(f"Loaded: {uploaded_file.name}")

        st.divider()
        if st.button("New Chat"):
            st.session_state.messages = []
            st.rerun()
        
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.rerun()

    # Chat History Container
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display History
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Chat Input
    if prompt := st.chat_input("Message Kairo..."):
        # If a file was uploaded, we can append its info to the prompt
        if uploaded_file:
            prompt = f"[User uploaded {uploaded_file.name}]\n\n" + prompt

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Grok AI Response
        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(
                    model=st.session_state.model,
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Save to Supabase Memory
                supabase.table("chats").insert({
                    "user_id": st.session_state.user_id,
                    "messages": st.session_state.messages
                }).execute()
            except Exception as e:
                st.error(f"Engine Error: {e}")
