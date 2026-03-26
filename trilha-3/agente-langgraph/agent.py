from dotenv import load_dotenv
load_dotenv()

import os
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_cohere import ChatCohere
from langchain_community.tools.tavily_search import TavilySearchResults

tool = TavilySearchResults(max_results=10, tavily_api_key=os.getenv("TAVILY_SEARCH_API"))

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # O operator.add significa que novas mensagens são concatenadas à lista existente (não substituem).

class Agent:
    def __init__(self, model, tools, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_cohere)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_cohere(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Chamando: {t}")
            if not t['name'] in self.tools:      # verificar nome de ferramenta incorreto do LLM
                print("\n ....nome de ferramenta incorreto....")
                result = "nome de ferramenta incorreto, tente novamente"  # instruir LLM a tentar novamente
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("De volta ao modelo!")
        return {'messages': results}
    
prompt = """Você é um assistente de pesquisa inteligente. Use o motor de busca para procurar informações. \
    Você pode fazer múltiplas chamadas (juntas ou em sequência). \
    Só procure informações quando tiver certeza do que quer. \
    Se precisar procurar algumas informações antes de fazer uma pergunta de acompanhamento, você pode fazer isso!
    """

agent = Agent(ChatCohere(model="command-a-03-2025", temperature=0), tools=[tool], system=prompt)

messages = [HumanMessage(content="Qual a musica em que o natanzinho lima mulher bonita e gado nelore?")]
result = agent.graph.invoke({"messages": messages})
print("Resultado completo:")
print(result)
print("\nResposta final:")
print(result['messages'][-1].content)

# É essencialmente um agente ReAct (Reason + Act): o LLM raciocina, decide se precisa de mais informação, age (busca), e repete até ter confiança para responder.