import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from chat_pdf import app
from langchain_core.messages import AIMessage, HumanMessage

st.set_page_config(page_title="PDFassistent", page_icon=":robot_face:", layout="wide")

st.title("Assistente de IA para PDFs")

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = [AIMessage(content="Olá! Faça upload de um arquivo PDF e me faça uma pergunta sobre o conteúdo para começar.")]

uploaded_file = st.file_uploader("Faça upload do seu arquivo PDF", type=["pdf"])

pdf_text = ""
if uploaded_file is not None:
    docs = PyPDFLoader(uploaded_file.name).load()
    pdf_text = "\n".join(doc.page_content for doc in docs)
    
    question = st.text_area("Digite sua pergunta sobre o conteúdo do PDF")

    if question:
        st.session_state['message_history'].append(HumanMessage(content=question))

        response = app.invoke({
            "question": question,
            "context": [{'page_content': pdf_text}]
        })

        st.session_state['message_history'].append(AIMessage(content=response['answer']))


for message in st.session_state['message_history']:
    if isinstance(message, HumanMessage):
        message_box = st.chat_message('user')    
    else:
        message_box = st.chat_message('assistant')
    message_box.markdown(message.content)