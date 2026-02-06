from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, List
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

class State(TypedDict):
    pergunta: str
    contexto: list
    resposta: str

def generate(state: State):
    docs_context = "\n\n".join([doc.page_content for doc in state.contexto])
    resposta = f"Pergunta: {state.pergunta}\n\nContexto: {docs_context}\n\nResposta:"
    return {"resposta": resposta}

template = "Você é um assistente de IA útil que ajuda os usuários a responder perguntas com base no contexto fornecido: {contexto} Pergunta: {pergunta} Resposta: "

prompt = PromptTemplate(
    input_variables=["pergunta", "contexto"],
    template=template,
)

llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
qna_chain = prompt | llm
graph_builder = StateGraph(State)
graph_builder.add_node("generate", generate)

graph_builder.set_entry_point("generate")
graph_builder.set_finish_point("generate")

loader = PyPDFLoader("aula-3/Inteligência-Artificial.pdf")
docs = loader.load()

contexto = docs
pergunta = "O que é inteligência artificial?"

response = app.invoke({"pergunta": pergunta, "contexto": contexto})

print(response["resposta"])