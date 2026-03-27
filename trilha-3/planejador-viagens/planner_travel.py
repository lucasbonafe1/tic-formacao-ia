from dotenv import load_dotenv
load_dotenv()

import os 
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from IPython.display import Image, display
from typing import TypedDict, Any
from prompts_const import QUERY_MAKER_PROMPT, RESULT_PROMPT, REVISION_PROMPT
from langchain_cohere import ChatCohere
from tools import calcular_orcamento

tools = [calcular_orcamento]
model = ChatCohere(model="command-a-03-2025", temperature=0).bind_tools(tools)
tavily = TavilySearchResults(max_results=3, tavily_api_key=os.getenv("TAVILY_SEARCH_API"))
tool_node = ToolNode(tools)

# Armazena o progresso e as variáveis do agente.
class AgentState(TypedDict):
    task: str # interesse do usuário
    queries: list[str] # consultas realizadas pelo agente
    draft: list[str] # rascunhos de respostas
    result: str # resultado final
    user_feedback: str # feedback do usuário
    revision_count: int # número de revisões realizadas
    messages: list[Any] # histórico de mensagens para ferramentas

class Queries(BaseModel):
    queries: list[str]

# O agente segue um ciclo de: Gerar Queries -> Buscar Informações -> Gerar Resultado -> Feedback do Usuário -> Revisão (se necessário)
def query_node(state: AgentState):
    # gera as queries com base no interesse do usuário e nas instruções do prompt
    messages = [    
        SystemMessage(content=QUERY_MAKER_PROMPT),
        HumanMessage(content=state["task"])
    ]
    response = model.with_structured_output(Queries).invoke(messages)
    return {"queries": response.queries}

def search_node(state: AgentState): # realiza buscas online com base nas queries geradas
    draft = state['draft'] or []
    for q in state['queries']:
        try:
            response = tavily.invoke({"query": q})
            # Extrai conteúdo de texto da resposta
            if isinstance(response, str):
                draft.append(response)
            elif isinstance(response, dict) and 'results' in response:
                for r in response['results']:
                    if isinstance(r, dict) and 'content' in r:
                        draft.append(r['content'])
                    elif isinstance(r, str):
                        draft.append(r)
            elif isinstance(response, list):
                for item in response:
                    if isinstance(item, str):
                        draft.append(item)
                    elif isinstance(item, dict) and 'content' in item:
                        draft.append(item['content'])
        except Exception as e:
            print(f"Error searching for query '{q}': {e}")
            continue
    return {"draft": draft}

def generate_result_node(state: AgentState): # gera o planejamento de viagem completo com base nas informações coletadas
    draft = "\n\n".join(state['draft'] or [])
    
    messages = [
        SystemMessage(content=RESULT_PROMPT.format(draft=draft, task=state['task'])),
        HumanMessage(content=f"Aqui estão o meu destino e interesses: {state['task']}")
    ]
    
    response = model.invoke(messages)
    
    # Se o modelo chamou uma ferramenta, armazena o histórico
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return {
            "messages": messages + [response],
            "result": ""
        }
    
    # Senão, retorna o resultado final
    return {
        "messages": messages + [response],
        "result": response.content
    }

def tools_executor_node(state: AgentState):
    """Executa as ferramentas chamadas pelo modelo"""
    if not state.get("messages"):
        return {"result": ""}
    
    messages = list(state["messages"])
    
    # Executa as ferramentas e coleta os resultados
    while messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        ai_message = messages[-1]
        
        for tool_call in ai_message.tool_calls:
            # Executa a ferramenta
            tool_result = tool_node.invoke({"messages": [ai_message]})
            if tool_result and "messages" in tool_result:
                messages.extend(tool_result["messages"])
        
        # Chama o modelo novamente com os resultados
        response = model.invoke(messages)
        messages.append(response)
    
    # Retorna o resultado final
    final_result = messages[-1].content if hasattr(messages[-1], 'content') else ""
    return {
        "messages": messages,
        "result": final_result
    }

def user_feedback_node(state: AgentState): # Busca o feedback do usuário sobre o planejamento gerado
    print("\n" + "=" * 60)
    print("🎯 SEU PLANO DE VIAGEM:")
    print("=" * 60)
    print(state['result'])
    print("=" * 60)
    
    print("\n💬 Você gostaria de fazer alguma alteração no plano?")
    print("Opções:")
    print("1. Digite suas sugestões de mudança")
    print("2. Digite 'ok' ou 'perfeito' para finalizar")
    print("3. Digite 'sair' para encerrar")
    
    feedback = input("\nSua resposta: ").strip()
    
    if feedback.lower() in ['ok', 'perfeito', 'finalizar', 'done']:
        return {"user_feedback": "Aprovado", "revision_count": state.get('revision_count', 0)}
    elif feedback.lower() in ['sair', 'exit', 'quit']:
        return {"user_feedback": "Sair", "revision_count": state.get('revision_count', 0)}
    else:
        return {"user_feedback": feedback, "revision_count": state.get('revision_count', 0) + 1}

def revision_node(state: AgentState): # Revise o planejamento de viagem com base no feedback do usuário
    if state['user_feedback'] in ['Aprovado', 'Sair']:
        return {"result": state['result']}
    
    draft_content = "\n\n".join(state['draft'] or [])
    
    messages = [
        SystemMessage(content=REVISION_PROMPT.format(
            current_result=state['result'],
            user_feedback=state['user_feedback'],
            task=state['task'],
            draft=draft_content
        )),
        HumanMessage(content="Por favor, revise o planejamento com base no feedback fornecido e nas informações disponíveis.")
    ]
    
    response = model.invoke(messages)
    return {"result": response.content}

def should_continue(state: AgentState): # Verifica se o processo deve continuar ou encerrar com base no feedback do usuário e no número de revisões
    if state['user_feedback'] == 'Sair':
        return "end"
    elif state['user_feedback'] == 'Aprovado':
        return "end"
    elif state.get('revision_count', 0) >= 3:
        print("\n⚠️  Limite de 3 revisões atingido. Finalizando...")
        return "end"
    else:
        return "feedback"

builder = StateGraph(AgentState)

# Nodes
builder.add_node("query", query_node)
builder.add_node("search", search_node)
builder.add_node("generate_result", generate_result_node)
builder.add_node("tools", tools_executor_node)
builder.add_node("user_feedback", user_feedback_node)
builder.add_node("revision", revision_node)

# Função para determinar se deve chamar ferramentas
def should_use_tools(state: AgentState):
    if not state.get("messages"):
        return "user_feedback"
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "user_feedback"

# Edges
builder.add_edge(START, "query")
builder.add_edge("query", "search")
builder.add_edge("search", "generate_result")
builder.add_conditional_edges(
    "generate_result",
    should_use_tools,
    {
        "tools": "tools",
        "user_feedback": "user_feedback"
    }
)
builder.add_edge("tools", "user_feedback")
builder.add_conditional_edges( # condição de feedback do usuário para decidir se continua ou encerra
    "user_feedback",
    should_continue,
    {
        "feedback": "revision",
        "end": END
    }
)
builder.add_edge("revision", "user_feedback")

checkpoint = InMemorySaver() # para armazenar o estado do agente entre as etapas

graph = builder.compile(checkpointer=checkpoint)

# Try to display the graph visualization
def display_graph():
    """Display the graph visualization if possible"""
    try:
        # Try to generate and display the graph
        graph_image = graph.get_graph().draw_mermaid_png()
        display(Image(graph_image))
        print("✅ Graph visualization generated successfully!")
    except Exception as e:
        print(f"⚠️  Could not generate graph visualization: {e}")
        print("This is optional and doesn't affect the functionality of the travel planner.")
        print("To enable graph visualization, install: pip install pygraphviz")

# Display the graph
display_graph()

# Run the travel planner
def run_travel_planner():
    """Run the travel planner with a sample query"""
    print("\n🚀 Starting Travel Planner with Human-in-the-Loop...")
    print("=" * 50)
    
    thread = {"configurable": {"thread_id": "1"}}
    
    initial_state = {
        'task': "Gostaria de viajar para o Japão, gosto de surfar, fazer esportes radicais e adoro cerveja. Me passe o orçamento aproximado para essa viagem e me faça um planejamento de viagem personalizado com base nesses interesses.",
        'draft': [],
        'queries': [],
        'result': "",
        'user_feedback': "",
        'revision_count': 0,
        'messages': []
    }
    
    print("📋 Processing your travel request...")
    print("\n" + "=" * 50)
    
    for step in graph.stream(initial_state, thread):
        if 'query' in step:
            print(f"🔍 Generated {len(step['query']['queries'])} search queries")
        elif 'search' in step:
            print(f"📚 Collected {len(step['search']['draft'])} information sources")
        elif 'result' in step:
            print("✅ Initial travel plan generated!")
        elif 'feedback' in step:
            if step['feedback']['user_feedback'] == 'Aprovado':
                print("\n🎉 Plano aprovado! Obrigado por usar o Travel Planner!")
            elif step['feedback']['user_feedback'] == 'Sair':
                print("\n👋 Obrigado por usar o Travel Planner!")
            else:
                print(f"🔄 Revisão #{step['feedback']['revision_count']} solicitada...")
        elif 'revision' in step:
            print("✅ Plano revisado com base no seu feedback e informações da pesquisa!")

if __name__ == "__main__":
    run_travel_planner()