import asyncio
import nest_asyncio
import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Apply nest_asyncio to allow nested asyncio.run() calls in Streamlit
nest_asyncio.apply()

from orchestrator_agent import orchestrator_agent, APP_NAME   # ← your import

# Session state initialization
if "session_service" not in st.session_state:
    st.session_state.session_service = InMemorySessionService()

if "session_id" not in st.session_state:
    import time
    st.session_state.session_id = f"ui_session_{int(time.time())}"

if "user_id" not in st.session_state:
    st.session_state.user_id = "pavan_ui"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Create session
async def ensure_session():
    await st.session_state.session_service.create_session(
        app_name=APP_NAME,
        user_id=st.session_state.user_id,
        session_id=st.session_state.session_id
    )

# Initialize runner once
if "runner" not in st.session_state:
    st.session_state.runner = Runner(
        agent=orchestrator_agent,
        session_service=st.session_state.session_service,
        app_name=APP_NAME,
    )
    asyncio.run(ensure_session())  # safe now with nest_asyncio

# UI Setup
st.set_page_config(page_title="Study Agent", layout="wide")

st.title("🤖 Personalized Study & Resource Agent")
st.caption("Tell me what you want to learn, your level, time available, and goal — I'll create a plan and find resources.")

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to study? (e.g. Terraform beginner 1 day job interview prep)"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response area
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("▍ Thinking...")

        try:
            user_message = types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )

            response_chunks = []   # ← use list instead of string + nonlocal

            async def stream_agent_response():
                try:
                    async for event in st.session_state.runner.run_async(
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.session_id,
                        new_message=user_message
                    ):
                        if hasattr(event, "content") and event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    chunk = part.text
                                    response_chunks.append(chunk)
                                    current_text = "".join(response_chunks)
                                    message_placeholder.markdown(current_text + " ▍")

                except AttributeError:
                    # Fallback 
                    events = st.session_state.runner.run(
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.session_id,
                        new_message=user_message
                    )
                    for event in events:
                        if hasattr(event, "content") and event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    full_response += part.text
                                    message_placeholder.markdown(full_response + " ▍")

            # Run the async streaming function safely
            asyncio.run(stream_agent_response())

            # Final clean response 
            full_response = "".join(response_chunks)
            message_placeholder.markdown(full_response or "**No content received**")

            # Save to history
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except Exception as e:
            error_text = f"**Error occurred:** {str(e)}"
            message_placeholder.error(error_text)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_text}
            )

# Sidebar
with st.sidebar:
    st.header("Session")
    st.caption(f"User: {st.session_state.user_id}")
    st.caption(f"Session ID: {st.session_state.session_id[:16]}...")

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption("Powered by Google ADK + Gemini + A2A agents")

# Debug expander for last response
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    with st.expander("Raw agent output (debug)"):
        st.code(st.session_state.messages[-1]["content"], language="markdown")