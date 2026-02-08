import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from chat_pdf import app
from langchain_core.messages import AIMessage, HumanMessage

st.set_page_config(page_title="PDFassistent", page_icon=":robot_face:", layout="wide")
st.title("Assistente de IA para PDFs")

if "message_history" not in st.session_state:
    content = "Olá! Faça upload de um arquivo PDF e me faça uma pergunta sobre o conteúdo para começar."
    st.session_state["message_history"] = [AIMessage(content=content)]
    with st.chat_message("assistant"):
        st.markdown(content)

uploaded_file = st.file_uploader("Faça upload do seu arquivo PDF", type=["pdf"])

if uploaded_file:
    docs = PyPDFLoader(uploaded_file.name).load()
    pdf_text = "\n".join(doc.page_content for doc in docs)

    question = st.text_area("Digite sua pergunta sobre o conteúdo do PDF")

    if question:
        st.session_state.message_history.append(HumanMessage(content=question))
        with st.chat_message("user"):
            st.markdown(question)

        response = app.invoke({
            "question": question,
            "context": [{"page_content": pdf_text}]
        })["answer"]

        full_response = ""
        message_box = st.chat_message("assistant")
        for chunk in message_box.write_stream(response):
            full_response += chunk

        # salva resposta FINAL da IA (string)
        st.session_state.message_history.append(
            AIMessage(content=full_response)
        )
