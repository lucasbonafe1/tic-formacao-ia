import re
import os

from dotenv import load_dotenv
load_dotenv()

import cohere

client = cohere.ClientV2()

class Agent:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        completion = client.chat(
                        model="command-a-03-2025", 
                        temperature=0,
                        messages=self.messages)
        return completion.message.content[0].text

def calculate(formula):
    return eval(formula)

def preco_prato(nome):
    if nome == "Feijoada":
        return "Uma Feijoada custa R$ 75,90"
    elif nome == "Moqueca":
        return "Uma Moqueca custa R$ 89,90"
    elif nome == "Picanha":
        return "Uma Picanha custa R$ 129,90"
    else:
        return "Prato não encontrado no cardápio"

known_actions = {
    "calculo": calculate,
    "calcular": calculate,
    "preco_prato": preco_prato
}

prompt = """
    Estamos em 23 de março de 2026. Você é um agente de IA que executa ações para responder perguntas.

    Você executa em um ciclo de Pensamento, Ação, PAUSA, Observação.
    No final do ciclo você fornece uma Resposta
    Use Pensamento para descrever seus pensamentos sobre a pergunta que foi feita.
    Use Ação para executar uma das ações disponíveis - então retorne PAUSA.
    Observação será o resultado da execução dessas ações.

    Suas ações disponíveis são:

    calcular:
    ex: calcular: 4 * 7 / 3
    Executa um cálculo e retorna o número - usa Python então certifique-se de usar sintaxe de ponto flutuante se necessário

    preco_prato:
    ex: preco_prato: Feijoada
    retorna o preço do prato quando fornecido o nome

    Exemplo de sessão:

    Pergunta: Quanto custa uma Moqueca?
    Pensamento: Devo verificar o preço da Moqueca usando preco_prato
    Ação: preco_prato: Moqueca
    PAUSA

    Você será chamado novamente com isto:

    Observação: Uma Moqueca custa R$ 89,90

    Você então fornece:

    Resposta: Uma Moqueca custa R$ 89,90
    """.strip()

action_re = re.compile('^Ação: (\\w+): (.*)$')

def query(question, max_turns=5):
    i = 0
    bot = Agent(prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        print(result)
        actions = [
            action_re.match(a) 
            for a in result.split('\n') 
            if action_re.match(a)
        ]
        print(actions)
        if actions:
            # Há uma ação para executar
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception("Ação desconhecida: {}: {}".format(action, action_input))
            print(" -- executando {} {}".format(action, action_input))
            observation = known_actions[action](action_input)
            print("Observação:", observation)
            next_prompt = "Observação: {}".format(observation)
        else:
            return
        
question = """Quantos anos tem alguém que nasceu em 1990 considerando o ano atual?"""
query(question)