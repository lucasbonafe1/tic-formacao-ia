import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_cohere import ChatCohere

from dotenv import load_dotenv
load_dotenv()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("Chatbot com Memória – Aula 2")
user_input = st.text_input("Digite sua pergunta:")
send = st.button("Enviar")

llm = ChatCohere(temperature=0.5, model="command-a-03-2025", streaming=True)

if send and user_input:
    st.session_state.chat_history.append(HumanMessage(content=user_input))

    response = llm.invoke(st.session_state.chat_history)

    st.session_state.chat_history.append(AIMessage(content=response.content))

    st.write(response.content)