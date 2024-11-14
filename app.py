 # Importing required packages
import streamlit as st
import openai
import uuid
import time
import io
from openai import OpenAI
import requests, os

#from langchain.llms import OpenAI

#Global Page Configuration
st.set_page_config(
    page_title="Nodo + Humanidades",
    page_icon="🧠",
    initial_sidebar_state="collapsed",
)

# Your chosen model
MODEL = "gpt-4o"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state:
    st.session_state.run = {"status": None}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0


# Initialize OpenAI client
client = OpenAI(
  base_url="https://oai.helicone.ai/v1", 
  default_headers={ 
    "Helicone-Auth": f"Bearer " + st.secrets["HELICONE_API_KEY"] ,
    "Helicone-Property-Session": st.session_state.session_id,
    #"Helicone-Property-Conversation": "Additional Feedback",
    "Helicone-Property-App": st.secrets["APP_NAME"],
  }
)


# Set up the page
#st.set_page_config(page_title="hacer.ai - Automatización")
st.sidebar.title("Nodo + Humanidades")
st.sidebar.divider()
st.sidebar.markdown("Mentor De Humanidades", unsafe_allow_html=True)
st.sidebar.markdown("hacer Agent Toolkit 1.0")
st.sidebar.divider()

st.write("""<img height="120" src="https://es.nodoeafit.com/wp-content/uploads/2024/11/HUMANIDADES.png"/>""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK, .stDeployButton, .stAppToolbar, 
    _viewerBadge_nim44_23, _profileContainer_51w34_53,  
    a[href$='https://share.streamlit.io/user/camilou'],
    a[href$='https://streamlit.io/cloud']    
    {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize OpenAI assistant
if "assistant" not in st.session_state:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])
    st.session_state.thread = client.beta.threads.create(
        metadata={'session_id': st.session_state.session_id}
    )

# Display chat messages
elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":
    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread.id
    )
    for message in reversed(st.session_state.messages.data):
        if message.role in ["user", "assistant"]:
            with st.chat_message(message.role):
                for content_part in message.content:
                    message_text = content_part.text.value
                    st.markdown(message_text)

# Chat input and message creation with file ID
if prompt := st.chat_input("¿Cómo puedo ayudarte con tu proceso de formación?"):
    with st.chat_message('user'):
        st.write(prompt)

    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": prompt
    }

    # Include file ID in the request if available
    if "file_id" in st.session_state:
        message_data["file_ids"] = [st.session_state.file_id]

    st.session_state.messages = client.beta.threads.messages.create(**message_data)

    st.session_state.run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id,
    )
    if st.session_state.retry_error < 3:
        time.sleep(1)
        st.rerun()

# Handle run status
if hasattr(st.session_state.run, 'status'):
    if st.session_state.run.status == "running":
        with st.chat_message('assistant'):
            st.write("Buscando Información ......")
        if st.session_state.retry_error < 3:
            time.sleep(1)
            st.rerun()

    elif st.session_state.run.status == "failed":
        st.session_state.retry_error += 1
        with st.chat_message('assistant'):
            if st.session_state.retry_error < 3:
                st.write("Run failed, retrying ......")
                time.sleep(3)
                st.rerun()
            else:
                st.error("FAILED: The OpenAI API is currently processing too many requests. Please try again later ......")

    elif st.session_state.run.status != "completed":
        st.session_state.run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread.id,
            run_id=st.session_state.run.id,
        )
        if st.session_state.retry_error < 3:
            time.sleep(3)
            st.rerun()
