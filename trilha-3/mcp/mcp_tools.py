import json
from jsonpath_ng import parse
from jsonpath_ng.exceptions import JSONPathError
from mcp.server import FastMCP

# Criar instância do servidor MCP
mcp = FastMCP("json-validator")


def validate_json(json_string: str) -> dict:
    """
    Valida se uma string contém um JSON bem formado.
    """
    try:
        json.loads(json_string)
        return {"valid": True, "error": None}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"JSON inválido: {str(e)}"}


def format_json(json_string: str) -> dict:
    """
    Formata o conteúdo para uma versão legível e indentada.
    """
    try:
        parsed = json.loads(json_string)
        pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
        return {"pretty": pretty, "error": None}
    except json.JSONDecodeError as e:
        return {"pretty": None, "error": f"Erro ao formatar JSON: {str(e)}"}


def extract_values(json_string: str, jsonpath_expr: str) -> dict:
    """
    Extrai valores da estrutura JSON utilizando expressões JSONPath.
    """
    try:
        parsed = json.loads(json_string)
        expr = parse(jsonpath_expr)
        matches = [match.value for match in expr.find(parsed)]
        
        if matches:
            return {"results": matches, "error": None}
        else:
            return {"results": [], "error": "Nenhum valor encontrado para a expressão JSONPath"}
    except json.JSONDecodeError as e:
        return {"results": None, "error": f"JSON inválido: {str(e)}"}
    except JSONPathError as e:
        return {"results": None, "error": f"Expressão JSONPath inválida: {str(e)}"}


@mcp.tool()
def jsonValidator(json_string: str, jsonpath_expr: str = None) -> dict:
    """
    Valida, formata e extrai valores de uma string JSON.
    
    Args:
        json_string: String contendo JSON a ser processado
        jsonpath_expr: Expressão JSONPath opcional para extrair valores
    
    Returns:
        Dicionário com campos: valid, error, pretty, results
    """
    # Validar JSON
    validation = validate_json(json_string)
    
    result = {
        "valid": validation["valid"],
        "error": validation["error"],
        "pretty": None,
        "results": None
    }
    
    # Se JSON é válido, formatar e extrair valores
    if validation["valid"]:
        # Formatar JSON
        formatting = format_json(json_string)
        result["pretty"] = formatting["pretty"]
        
        # Extrair valores se JSONPath foi fornecido
        if jsonpath_expr:
            extraction = extract_values(json_string, jsonpath_expr)
            result["results"] = extraction["results"]
            if extraction["error"]:
                result["error"] = extraction["error"]
    
    return result