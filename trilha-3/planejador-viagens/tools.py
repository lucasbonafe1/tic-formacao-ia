from dotenv import load_dotenv
load_dotenv()
import os 
import requests
from langchain_core.tools import tool

def busca_previsao_tempo(pais: str) -> str:
    webhook_url = os.getenv("WEBHOOK-N8N")
    payload = {
        "pais": pais
    }
    try:
        response = requests.post(webhook_url, json=payload)
        return response.json()
    except Exception as e:
        return f"❌ Erro ao conectar com o serviço de previsão do tempo: {str(e)}"
    
@tool 
def sugerir_bagagem_com_base_no_clima(pais: str) -> str:
    """
    Sugere o que empacotar na bagagem baseado no clima do país.
    
    Args:
        pais: O nome do país
    
    Returns:
        Sugestões de bagagem baseadas nas condições climáticas do país
    """
    response = busca_previsao_tempo(pais)
    if not isinstance(response, dict) or 'main' not in response:
        return f"Não foi possível obter a previsão do tempo para {pais}."
    
    forecast = response['main']
    suggestions = []
    if forecast.get('temp_max') > 25:
        suggestions.append("Roupas leves, protetor solar e óculos de sol")
    if forecast.get('temp_min') < 20:
        suggestions.append("Roupas quentes e agasalhos")
    if forecast.get('humidity') > 100:
        suggestions.append("Guarda-chuva ou capa de chuva")
    if response['wind'].get('speed', 0) > 2:
        suggestions.append("Jaqueta corta-vento")
    return f"Sugestões de bagagem para {pais}: {', '.join(suggestions)}"