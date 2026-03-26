from langchain_core.tools import tool

@tool
def calcular_orcamento(destino: str, interesses: str) -> str:
    """
    Calcula o orçamento aproximado de uma viagem baseado no destino e interesses.
    
    Args:
        destino: O nome do destino da viagem
        interesses: Os interesses e preferências do viajante
    
    Returns:
        Uma estimativa de orçamento para a viagem
    """
    if "Japão" in destino:
        base = 3000
        if "surf" in interesses.lower():
            base += 500
        if "esportes radicais" in interesses.lower():
            base += 700
        if "cerveja" in interesses.lower():
            base += 300
        return f"💰 Orçamento aproximado para uma viagem ao {destino}: R$ {base:.2f}\n- Incluindo hospedagem, transporte local e atividades conforme seus interesses (surf, esportes radicais, bares de cerveja)"
    else:
        return f"⚠️  Orçamento não disponível para o destino '{destino}'. Por favor, tente outro destino ou forneça mais informações."