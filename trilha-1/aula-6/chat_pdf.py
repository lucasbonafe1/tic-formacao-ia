from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph
from typing import TypedDict

from dotenv import load_dotenv
load_dotenv()

template = "Você é um assistente de IA útil que ajuda os usuários a responder perguntas com base no contexto fornecido: {context} Pergunta: {question}"

prompt = ChatPromptTemplate.from_template(template)

llm = ChatCohere(temperature=0.5, model="command-a-03-2025", streaming=True)

qna_chain = prompt | llm

class State(TypedDict):
    question: str
    context: list
    answer: str

graph = StateGraph(State)

# A cada etapa do processo, essa função é chamada para gerar a resposta com base no estado atual, que inclui a pergunta e o contexto. A resposta é então armazenada no estado para ser exibida ao usuário.
def generate(state: State) -> State:
    docs_context = "\n".join(doc["page_content"] for doc in state["context"])

    response = qna_chain.stream({
        "context": docs_context,
        "question": state["question"],
        "answer": ""
    })

    return {"answer": response}

# Cria um nó do método e o chama
graph.add_node("generate", generate)

# Define o ponto de entrada e o ponto de término do gráfo. O ponto de entrada é onde o processo começa, 
# e o ponto de término é onde ele termina. Neste caso, ambos são definidos como "generate", indicando que o processo começa e termina com a geração da resposta.
graph.set_entry_point("generate")
graph.set_finish_point("generate")

app = graph.compile()