import streamlit as st
import requests
import json
import yaml
import time
from pathlib import Path
import base64
import os

# Constants
CREDENTIALS_FILE = Path(".streamlit/credentials.yaml")
CHAT_HISTORY_DIR = Path("chat_histories")
APP_NAME = 'Chatbot with OpenRouter'
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-pro-1.5-exp"

# Ensure chat history directory exists
CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# Utility Functions
def load_credentials():
    """Load credentials from a YAML file."""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, "r") as file:
            return yaml.safe_load(file)
    return {}

def save_credentials(username, api_key):
    """Save credentials to a YAML file."""
    credentials = load_credentials()
    credentials[username] = api_key
    with open(CREDENTIALS_FILE, "w") as file:
        yaml.dump(credentials, file)

def verify_api_key(api_key):
    """Verify API key by making a test request."""
    response = requests.post(
        url=API_URL,
        headers={"Authorization": f"Bearer {api_key}", "X-Title": APP_NAME},
        data=json.dumps({"model": MODEL_NAME, "messages": []})
    )
    return response.status_code == 200

def send_chat_request(api_key, messages):
    """Send chat request to OpenRouter and get assistant's response."""
    response = requests.post(
        url=API_URL,
        headers={"Authorization": f"Bearer {api_key}", "X-Title": APP_NAME},
        data=json.dumps({"model": MODEL_NAME, "messages": messages})
    )
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        st.error("API call failed.")
        return None

def display_chat_message(role, content, typing_speed=0.05):
    """Display chat message with typing effect for the assistant."""
    with st.chat_message(role):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in content.splitlines():
            for word in chunk.split():
                full_response += word + " "
                message_placeholder.markdown(full_response)
                time.sleep(typing_speed)
            full_response += "\n"
        message_placeholder.markdown(full_response)

# JSON Chat History Functions
def get_user_chat_file(username):
    """Get the path to the user's chat history file."""
    return CHAT_HISTORY_DIR / f"{username}_chat_history.json"

def load_chat_history(username):
    """Load chat history from JSON file."""
    chat_file = get_user_chat_file(username)
    if chat_file.exists():
        with open(chat_file, "r") as file:
            return json.load(file)
    return []

def save_chat_history(username, chat_histories):
    """Save chat history to JSON file."""
    chat_file = get_user_chat_file(username)
    with open(chat_file, "w") as file:
        json.dump(chat_histories, file)

def delete_chat_history(username, index):
    """Delete a specific chat history."""
    chat_histories = load_chat_history(username)
    if 0 <= index < len(chat_histories):
        del chat_histories[index]
        save_chat_history(username, chat_histories)
        return True
    return False

# App Initialization
def initialize_session_state():
    """Initialize session states for chat histories and messages."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_chat_index" not in st.session_state:
        st.session_state.current_chat_index = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

def authenticate_user():
    """Handle user login and sign-up functionality using tabs."""
    st.subheader("Welcome! Please log in or sign up to start chatting.")

    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # Login Tab
    with tab1:
        st.write("Log in with your username if you have already signed up.")
        username = st.text_input("Username", key="login_username")

        if st.button("Login", key="login_button"):
            credentials = load_credentials()
            if username in credentials:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.api_key = credentials[username]
                st.success("Login successful!")
                st.rerun()  # Redirect to chat interface
            else:
                st.error("Username not found. Please sign up first.")

    # Sign-Up Tab
    with tab2:
        st.write("Sign up with a new username and API key.\nThe API key can be obtained from [OpenRouter](https://openrouter.ai).")
        username = st.text_input("Username", key="signup_username")
        api_key = st.text_input("API Key", type="password", key="signup_api_key")

        if st.button("Sign Up", key="signup_button"):
            credentials = load_credentials()
            if username in credentials:
                st.error("Username already exists. Please choose a different username.")
            elif verify_api_key(api_key):
                save_credentials(username, api_key)
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.api_key = api_key
                st.success("Sign-up successful!")
                st.rerun()  # Redirect to chat interface
            else:
                st.error("Invalid API key. Please check your API key.")

def truncate_text(text, max_length):
    """Truncate text to a maximum length and add ellipsis if necessary."""
    return (text[:max_length] + '...') if len(text) > max_length else text

def sidebar_controls():
    """Controls for loading, starting new chats, and deleting chat histories in the sidebar."""
    st.sidebar.header("Chat Controls")
    
    if st.sidebar.button("Start New Chat", key="start_new_chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_index = None
        st.rerun()

    st.sidebar.header("Chat Histories")
    chat_histories = load_chat_history(st.session_state.username)
    for idx, history in enumerate(chat_histories):
        col1, col2 = st.sidebar.columns([6, 1])
        with col1:
            # Get the first message content (limited to one line)
            first_message = history[0]["content"] if history else "Empty chat"
            # Truncate the message to fit in one line (approximately 20 characters)
            truncated_message = truncate_text(first_message, 20)
            if st.button(truncated_message, key=f"load_chat_{idx}", use_container_width=True):
                st.session_state.messages = history
                st.session_state.current_chat_index = idx
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_chat_{idx}"):
                if delete_chat_history(st.session_state.username, idx):
                    st.success(f"Chat {idx + 1} deleted.")
                    if st.session_state.current_chat_index == idx:
                        st.session_state.messages = []
                        st.session_state.current_chat_index = None
                    st.rerun()
                else:
                    st.error("Failed to delete.")
        
        # Add a small vertical space between chat history buttons
        st.sidebar.markdown("<br>", unsafe_allow_html=True)

    # Add Sign Out button at the bottom of the sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("Sign Out", key="sign_out", use_container_width=True):
        for key in ["authenticated", "username", "api_key", "messages", "current_chat_index", "uploaded_file"]:
            st.session_state.pop(key, None)
        st.rerun()  # Redirect to login interface

def display_chat_history():
    """Display previous chat messages in the main chat area."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_file_upload():
    """Handle file upload functionality."""
    with st.expander("Upload a file", expanded=False):
        uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "png", "jpg", "jpeg"])
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            file_contents = uploaded_file.read()
            file_type = uploaded_file.type

            if file_type.startswith('image'):
                # Handle image files
                encoded_image = base64.b64encode(file_contents).decode('utf-8')
                st.image(file_contents, caption="Uploaded Image", use_column_width=True)
                return [{
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{file_type};base64,{encoded_image}"
                    }
                }]
            else:
                # Handle text-based files
                try:
                    text_content = file_contents.decode('utf-8')
                    st.text_area("File Contents", text_content, height=200)
                    return [{"type": "text", "text": f"File contents:\n\n{text_content}"}]
                except UnicodeDecodeError:
                    st.error("Unable to decode the file. Please upload a valid text or image file.")
                    return None
    return None

def handle_new_message(prompt, file_content=None):
    """Handle a new user message, get assistant's response, and update chat."""
    message_content = prompt
    if file_content:
        message_content += "\n\n[File content included]"

    st.session_state.messages.append({"role": "user", "content": message_content})

    # Send chat request and get assistant response
    assistant_response = send_chat_request(
        st.session_state.api_key,
        [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    )

    if assistant_response:
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        # Update chat history
        chat_histories = load_chat_history(st.session_state.username)
        if st.session_state.current_chat_index is not None:
            chat_histories[st.session_state.current_chat_index] = st.session_state.messages
        else:
            chat_histories.append(st.session_state.messages)
            st.session_state.current_chat_index = len(chat_histories) - 1
        
        save_chat_history(st.session_state.username, chat_histories)

# Main Application
def main():
    st.set_page_config(page_title="AI Chatbot", page_icon="🤖")

    st.title("🤖 AI Chatbot with OpenRouter")
    initialize_session_state()

    if not st.session_state.authenticated:
        authenticate_user()
    else:
        sidebar_controls()
        
        st.markdown(f"Welcome, **{st.session_state.username}**! 👋")
        
        file_content = handle_file_upload()
        
        # Display chat history
        for message in st.session_state.messages:
            display_chat_message(message["role"], message["content"])

        if prompt := st.chat_input("Type your message here..."):
            handle_new_message(prompt, file_content)
            st.rerun()  # Rerun the app to update the chat display

if __name__ == "__main__":
    main()