import streamlit as st
import requests
import json
import toml
import time

secrets = toml.load(".streamlit/secrets.toml")

st.title("Chat Bot with OpenRouter")

api_key = secrets["API_KEY"]
app_name = 'Chatbot with OpenRouter'

# Khởi tạo session state cho lưu trữ chat history
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = None

# Sidebar
st.sidebar.header("Chat Histories")

# Hiển thị các cuộc trò chuyện trong lịch sử
for idx, history in enumerate(st.session_state.chat_histories):
    if st.sidebar.button(f"Load Chat {idx + 1}", key=f"load_chat_{idx}"):
        st.session_state.messages = history
        st.session_state.current_chat_index = idx
        st.rerun()

# Nút "Start New Chat"
if st.sidebar.button("Start New Chat", key="start_new_chat"):
    if not st.session_state.messages or len(st.session_state.messages) > 0:
        st.session_state.messages = []
        st.session_state.current_chat_index = None
        st.rerun()

# Hiển thị các tin nhắn trước đó
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Khi người dùng nhập một câu hỏi mới
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gửi request tới OpenRouter API
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-Title": app_name,
        },
        data=json.dumps({
            "model": "google/gemini-pro-1.5-exp",
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

        # Tạo một chat message cho assistant ngay lập tức
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # Hiển thị từng ký tự một để tạo hiệu ứng chữ chạy
            for chunk in assistant_response.splitlines():  # Duyệt từng dòng
                for word in chunk.split():  # Duyệt từng từ trong dòng
                    full_response += word + " "
                    message_placeholder.markdown(full_response)  # Cập nhật nội dung tin nhắn
                    time.sleep(0.05)  # Thời gian delay giữa các từ
                full_response += "\n"  # Thêm ký tự xuống dòng sau mỗi dòng
                message_placeholder.markdown(full_response)  # Cập nhật lại để hiển thị dòng mới

        # Lưu lại phản hồi vào session
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        # Cập nhật lịch sử chat
        if st.session_state.current_chat_index is not None:
            st.session_state.chat_histories[st.session_state.current_chat_index] = st.session_state.messages
        else:
            st.session_state.chat_histories.append(st.session_state.messages)
            st.session_state.current_chat_index = len(st.session_state.chat_histories) - 1

    else:
        st.error(f"API call failed: {response.status_code}")
