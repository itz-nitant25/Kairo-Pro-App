import streamlit as st
from openai import OpenAI
from supabase import create_client

# --- 1. CONFIG ---
st.set_page_config(page_title="Kairo Pro", page_icon="🤖")

# --- 2. CONNECTIONS ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- 3. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "trial_count" not in st.session_state: st.session_state.trial_count = 0
if "user_email" not in st.session_state: st.session_state.user_email = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🤖 Kairo OpenAI")
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    if not st.session_state.user_email:
        st.info(f"Free Messages: {50 - st.session_state.trial_count}")
        email = st.text_input("Email to save history")
        if st.button("Login"):
            supabase.auth.sign_in_with_otp({"email": email})
            st.success("Link sent!")
    else:
        st.success(f"User: {st.session_state.user_email}")

# --- 5. CHAT LOGIC ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Message Kairo..."):
    # Check Trial
    if not st.session_state.user_email and st.session_state.trial_count >= 50:
        st.error("Trial limit reached! Please login.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Use the efficient 4o-mini model
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # History Logic
            if st.session_state.user_email:
                supabase.table("chats").insert({"email": st.session_state.user_email, "messages": st.session_state.messages}).execute()
            else:
                st.session_state.trial_count += 1
        except Exception as e:
            st.error(f"OpenAI Error: {e}")
