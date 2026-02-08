from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from langchain_cohere import ChatCohere

st.title("Assistente de IA com Streamlit")
prompt = st.text_area("Digite sua pergunta aqui:")

if st.button("Enviar"):
    if prompt:
        llm = ChatCohere(model="command-a-03-2025", temperature=0.4)
        response = llm.invoke(prompt)
        st.write("Resposta:", response.content)
    else:
        st.warning("Por favor, insira uma pergunta antes de enviar.")