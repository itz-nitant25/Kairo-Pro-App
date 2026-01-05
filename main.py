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
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚡ Kairo Pro")
    
    if not st.session_state.user_email:
        remaining = 50 - st.session_state.trial_count
        st.info(f"🎁 Guest Trial: {remaining} messages left")
        
        st.subheader("Login / Sign Up")
        email_input = st.text_input("Enter your Email")
        if st.button("Send Magic Link"):
            # This sends a login link to their inbox via Supabase
            res = supabase.auth.sign_in_with_otp({"email": email_input})
            st.success("Check your email for the login link!")
    else:
        st.success(f"Logged in: {st.session_state.user_email}")
        if st.button("Log Out"):
            st.session_state.user_email = None
            st.rerun()
        
        st.divider()
        st.subheader("📜 Chat History")
        # Fetch chats for this email
        history = supabase.table("chats").select("*").eq("email", st.session_state.user_email).order("created_at", desc=True).limit(10).execute()
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
    if not st.session_state.user_email and st.session_state.trial_count >= 50:
        st.error("Trial limit reached! Please log in via email to continue.")
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(model="grok-2-1212", messages=st.session_state.messages)
        ans = response.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    if not st.session_state.user_email:
        st.session_state.trial_count += 1
    else:
        supabase.table("chats").insert({
            "email": st.session_state.user_email,
            "messages": st.session_state.messages
        }).execute()
