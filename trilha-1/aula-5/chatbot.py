from dotenv import load_dotenv
load_dotenv()

from langchain_cohere import ChatCohere
from langchain.prompt import ChatPromptTemplate
from langgraph.graph import StateGraph
from langgraph.graph.message import MessageState

prompt = "Você é um assistente virtual especializado em responder perguntas sobre programação. Seja amigável e prestativo. Se possível use emojis para tornar a conversa mais leve e divertida, para melhorar o aprendizado."

chat_template = ChatPromptTemplate.from_messages([
    ("system", prompt),
    ("placeholder", "{messages}")
])

llm = ChatCohere(model="command-a-03-2025", temperature=0.4)

llm_with_prompt = chat_template | llm

def call_chat(message_state: MessageState) -> str:
    response = llm_with_prompt.invoke(message_state)

    return {
        'messages': [response]
    }

graph = StateGraph(MessageState)

graph.add_node('chat', call_chat)
graph.set_entry_point('chat')

app = graph.compile()