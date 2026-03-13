import streamlit as st
from langgraph_database_backend import chatbot, retriev_all_threads
from langchain_core.messages import HumanMessage
import uuid


def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(thread_id)

def load_conversation(thread_id):
    values = chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values
    if 'messages' in values.keys():
        return values['messages']
    else :
        return []



if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_thread' not in st.session_state:
    st.session_state['chat_thread'] = retriev_all_threads()

add_thread(st.session_state['thread_id'])



CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}



st.sidebar.title("LanhGraph ChatBot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_thread'] :
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for message in messages:
            if isinstance(message, HumanMessage):
                role='user'
            else:
                role='ai'
            temp_messages.append({'role': role, 'content': message.content})

        st.session_state['message_history'] = temp_messages


user_input = st.chat_input('Type Here ')

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if user_input:

    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('ai'):
        ai_message = st.write_stream(
                message_chunk.content for message_chunk, metadata in chatbot.stream(
                    {'messages': [HumanMessage(content=user_input)]},
                    config=CONFIG,
                    stream_mode='messages'
                )
        )
    st.session_state['message_history'].append({'role': 'ai', 'content': ai_message})
