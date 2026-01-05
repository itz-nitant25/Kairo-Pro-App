import streamlit as st
from openai import OpenAI
from supabase import create_client

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Kairo Pro", page_icon="⚡", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp {background-color: #0b0f19;}
    .sidebar .stButton>button {width: 100%; border-radius: 5px; margin-bottom: 5px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECTIONS ---
try:
    client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Setup Error: Check your Streamlit Secrets.")
    st.stop()

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "trial_count" not in st.session_state:
    st.session_state.trial_count = 0
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚡ Kairo Pro")
    
    if st.button("➕ New Chat / Reset"):
        st.session_state.messages = []
        st.rerun()
        
    st.divider()

    if not st.session_state.user_email:
        remaining = 50 - st.session_state.trial_count
        st.info(f"🎁 Guest Trial: {max(0, remaining)} left")
        
        email_input = st.text_input("Enter Email for History")
        if st.button("Send Magic Link"):
            try:
                supabase.auth.sign_in_with_otp({"email": email_input})
                st.success("Check your inbox!")
            except:
                st.error("Failed to send link.")
    else:
        st.success(f"Logged in: {st.session_state.user_email}")
        if st.button("Log Out"):
            st.session_state.user_email = None
            st.rerun()
        
        st.subheader("📜 History")
        history = supabase.table("chats").select("*").eq("email", st.session_state.user_email).order("created_at", desc=True).limit(8).execute()
        for chat in history.data:
            label = chat['messages'][0]['content'][:20] + "..." if chat['messages'] else "Old Chat"
            if st.button(label, key=chat['id']):
                st.session_state.messages = chat['messages']
                st.rerun()

# --- 5. CHAT TERMINAL ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Command Kairo..."):
    # Trial check
    if not st.session_state.user_email and st.session_state.trial_count >= 50:
        st.error("Limit reached. Please log in.")
        st.stop()
    
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant Response with Error Handling
    with st.chat_message("assistant"):
        try:
            # SANITIZER: Clean messages to prevent BadRequestError
            clean_history = [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages 
                if m.get("content") and str(m["content"]).strip() != ""
            ]

            response = client.chat.completions.create(
                model="grok-2-1212", 
                messages=clean_history
            )
            
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

            # Save Logic
            if not st.session_state.user_email:
                st.session_state.trial_count += 1
            else:
                supabase.table("chats").insert({
                    "email": st.session_state.user_email,
                    "messages": st.session_state.messages
                }).execute()
        
        except Exception as e:
            st.error(f"Engine Error: {str(e)}")
            if "BadRequestError" in str(e):
                st.warning("The conversation history caused a conflict. Click 'New Chat' to fix.")
