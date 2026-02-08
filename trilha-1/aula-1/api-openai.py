from openai import OpenAI

print("Acessando Cliente...")
client = OpenAI(
  base_url="http://139.82.24.30:1234/v1",
  api_key="lm-studio"
)

print("Cliente acessado com sucesso.")
print("Enviando requisição e aguardando retorno...")
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
       {"role": "system", "content": "Você é um entendedor expert em como o mundo se formou no que é hoje."},
       {"role": "user", "content": "Conte a historia do mundo."},
    ],
    temperature=1.0,
    stream=True,
)

print(completion.choices[0].message.content)