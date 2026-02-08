from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

import langchain
import getpass
import os

model = init_chat_model("gpt-4o-mini", model_provider="openai")

messages = [
    SystemMessage("Você é um tradutor profissional e fará a tradução correta de tudo que eu enviar para inglês."),
    HumanMessage("Hello, Good morning! How are you today?"),
]

response = model.invoke(messages)
print(response.content)