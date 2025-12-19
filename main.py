import streamlit as st
from openai import OpenAI
from supabase import create_client

# --- 1. CLOAKING (Hides Streamlit UI) ---
st.set_page_config(page_title="Kairo Pro", page_icon="⚡", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

# --- 2. CONNECTIONS ---
try:
    client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Setup Secrets in Streamlit Settings.")
    st.stop()

# --- 3. PASSWORDLESS LOGIN LOGIC ---
# Using Streamlit's native user tracking instead of custom tables
if not st.experimental_user.is_logged_in:
    st.title("🤖 Welcome to Kairo")
    st.write("Click below to enter your private AI terminal.")
    if st.button("Log in with Google"):
        st.login("google")
    st.stop()

# --- 4. KAIRO INTERFACE (Only visible if logged in) ---
user_email = st.experimental_user.email

with st.sidebar:
    st.write(f"Logged in: **{user_email}**")
    model_choice = st.selectbox("Grok Engine", ["grok-2", "grok-beta"])
    uploaded_file = st.file_uploader("📎 Analyze File", type=['txt', 'pdf', 'png', 'jpg'])
    
    # Load Past Chats from Supabase
    st.divider()
    st.subheader("📜 Past Chats")
    past_chats = supabase.table("chats").select("*").eq("email", user_email).order("created_at", desc=True).limit(5).execute()
    for chat in past_chats.data:
        if st.button(f"Chat {chat['created_at'][:10]}", key=chat['id']):
            st.session_state.messages = chat['messages']

    if st.button("Log Out"):
        st.logout()

# --- 5. CHAT SYSTEM ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Message Kairo..."):
    if uploaded_file:
        prompt = f"[File Attached: {uploaded_file.name}]\n\n" + prompt
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        resp = client.chat.completions.create(
            model=model_choice,
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        )
        answer = resp.choices[0].message.content
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Auto-save to Supabase using email as the ID
        supabase.table("chats").insert({
            "email": user_email,
            "messages": st.session_state.messages
        }).execute()
