import streamlit as st
from chatbot import app
from langchain_core.messages import AIMessage, HumanMessage

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(layout="wide", page_title="Chatbot de programação", page_icon="🤖")

st.title("🤖 Chatbot de Programação - Assistente Virtual")

if 'message_history' not in st.session_state:
    st.session_state.message_history = [AIMessage(content="Olá! Eu sou o assistente virtual de programação. Como posso ajudar você hoje?")]

user_input = st.chat_input("Digite sua mensagem aqui:")

if user_input:
    st.session_state.message_history.append(HumanMessage(content=user_input))

    response = app.invoke({
        'messages': st.session_state.message_history
    })

    st.session_state.message_history = response['messages']

for message in st.session_state.message_history:
    if isinstance(message, HumanMessage):
        st.chat_message("user").write(message.content)
    elif isinstance(message, AIMessage):
        st.chat_message("assistant").write(message.content)