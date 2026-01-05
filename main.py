import streamlit as st
from openai import OpenAI
from supabase import create_client

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Kairo Pro", page_icon="⚡", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

# --- 2. CONNECTIONS ---
client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "trial_count" not in st.session_state:
    st.session_state.trial_count = 0

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚡ Kairo Pro")
    
    if not st.user.is_logged_in:
        remaining = 50 - st.session_state.trial_count
        st.info(f"🎁 Guest Trial: {remaining} messages left")
        if st.button("Log in with Google"):
            st.login("google")
    else:
        st.success(f"Logged in: {st.user.email}")
        if st.button("Log Out"):
            st.logout()
        
        st.divider()
        st.subheader("📜 Chat History")
        # Fetch chats from Supabase for this user
        history = supabase.table("chats").select("*").eq("email", st.user.email).order("created_at", desc=True).limit(10).execute()
        for chat in history.data:
            label = chat['messages'][0]['content'][:25] + "..."
            if st.button(label, key=chat['id']):
                st.session_state.messages = chat['messages']
                st.rerun()

# --- 5. CHAT TERMINAL ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask Kairo anything..."):
    # Trial Limit Logic
    if not st.user.is_logged_in and st.session_state.trial_count >= 50:
        st.error("Trial limit (50 messages) reached! Please log in with Google to continue.")
        st.stop()
    
    # Display User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant Response
    with st.chat_message("assistant"):
        response = client.chat.completions.create(model="grok-2-1212", messages=st.session_state.messages)
        ans = response.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # Saving Logic
    if not st.user.is_logged_in:
        st.session_state.trial_count += 1
    else:
        supabase.table("chats").insert({
            "email": st.user.email,
            "messages": st.session_state.messages
        }).execute()
