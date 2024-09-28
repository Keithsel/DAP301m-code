import streamlit as st
import requests
import json
import toml 

secrets = toml.load(".streamlit/secrets.toml")

st.title("Chat Bot with OpenRouter")

api_key = secrets["API_KEY"]
app_name = 'Chatbot with OpenRouter'

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị các tin nhắn trước đó
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Khi người dùng nhập một câu hỏi mới
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gửi request tới OpenRouter API
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-Title": app_name,  # Optional
        },
        data=json.dumps({
            "model": "google/gemini-pro-1.5-exp",  # Optional, có thể thay đổi model tùy ý
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
        })
    )

    # Xử lý phản hồi từ API
    if response.status_code == 200:
        result = response.json()
        assistant_response = result["choices"][0]["message"]["content"]

        # Hiển thị phản hồi của assistant
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

        # Lưu lại phản hồi vào session
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    else:
        st.error(f"API call failed: {response.status_code}")
