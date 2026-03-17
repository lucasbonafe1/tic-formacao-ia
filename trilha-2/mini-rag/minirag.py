from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WikipediaLoader
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END
from typing import TypedDict

docs_ia = WikipediaLoader(query="Inteligência Artificial", load_max_docs=2, lang="pt").load()
docs_internet = WikipediaLoader(query="História da Internet", load_max_docs=2, lang="pt").load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       
    chunk_overlap=200,     
    length_function=len,
)   

chunks_ia = text_splitter.split_text(docs_ia[0].metadata['summary'])
chunks_internet = text_splitter.split_text(docs_internet[0].metadata['summary'])

embeddings = HuggingFaceEmbeddings(model_name="mixedbread-ai/mxbai-embed-large-v1")

all_chunks = chunks_ia + chunks_internet

vectorstore = Chroma.from_texts(
    texts=all_chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="wikipedia_docs"
)

print(f"Banco vetorial criado com {vectorstore._collection.count()} documentos.\n")

class State(TypedDict):
    question: str
    context: list[str]
    answer: str

llm = ChatCohere(temperature=0.5, model="command-a-03-2025")

# Nó 1: Busca no banco vetorial
def retrieve(state: State) -> dict:
    results = vectorstore.similarity_search(state["question"], k=3)
    docs = [doc.page_content for doc in results]
    return {"context": docs}

# Nó 2: Inclusão de contexto no prompt e geração de resposta
def augment_prompt(state: State) -> dict:
    context_text = "\n\n".join(state["context"])
    template = ChatPromptTemplate.from_template(
        "Você é um assistente útil. Use SOMENTE o contexto abaixo para responder.\n"
        "Inclua citações relevantes do texto na sua resposta.\n\n"
        "Contexto:\n{context}\n\n"
        "Pergunta: {question}\n\n"
        "Resposta:"
    )
    chain = template | llm
    response = chain.invoke({"context": context_text, "question": state["question"]})
    return {"answer": response.content}

# Nó 3: Exibição da resposta
def display(state: State) -> dict:
    print(state["answer"])
    print("\nFontes utilizadas:")
    for i, ctx in enumerate(state["context"], 1):
        print(f"  [{i}] {ctx[:100]}...")
    return {}

graph = StateGraph(State)
graph.add_node("retrieve", retrieve)
graph.add_node("augment_prompt", augment_prompt)
graph.add_node("display", display)

graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "augment_prompt")
graph.add_edge("augment_prompt", "display")
graph.add_edge("display", END)

app = graph.compile()
# Executa pergunta de teste
print("\nExecutando pergunta no grafo RAG...")
app.invoke({"question": "Quando surgiu o termo Inteligência Artificial?", "context": [], "answer": ""})