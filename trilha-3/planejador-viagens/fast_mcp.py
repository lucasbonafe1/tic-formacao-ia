from dotenv import load_dotenv 
load_dotenv()
import os
import httpx
import json
from typing import Optional
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError


# Inicializar servidor FastMCP
mcp = FastMCP(name="poi-finder")

# Configuração
OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")
OPENTRIPMAP_BASE_URL = "https://api.opentripmap.com"
MAX_DESCRIPTION_LENGTH = 500  # Truncate descriptions para LLM


@mcp.tool()
def poi_find(
    latitude: float,
    longitude: float,
    radius: int = 5000,
    kinds: Optional[str] = None,
) -> dict:
    """
    Encontra Points of Interest (POIs) em um raio especificado usando OpenTripMap.
    
    Args:
        latitude: Latitude do centro de busca (em graus decimais, ex: -23.5505).
        longitude: Longitude do centro de busca (em graus decimais, ex: -46.6333).
        radius: Raio de busca em metros (padrão: 5000). Máximo recomendado: 10000.
        kinds: Filtro de tipos de POIs (ex: "museums,interesting_places,tourist_check").
               Se None, retorna todos os tipos. Ver documentação para lista completa.
    
    Returns:
        dict com estrutura:
        {
            "success": bool,
            "count": int,
            "pois": [
                {
                    "xid": str,
                    "name": str,
                    "kinds": str,
                    "description": str (truncado),
                    "feature_class": str,
                    "preview": {
                        "source": str,
                        "picture": str
                    }
                },
                ...
            ]
        }
    
    Raises:
        ToolError: Se a API retornar erro ou validação falhar.
    """
    
    if not (-90 <= latitude <= 90):
        raise ToolError(f"Latitude inválida: {latitude}. Deve estar entre -90 e 90.")
    
    if not (-180 <= longitude <= 180):
        raise ToolError(f"Longitude inválida: {longitude}. Deve estar entre -180 e 180.")
    
    if radius < 100 or radius > 50000:
        raise ToolError(f"Raio inválido: {radius}. Deve estar entre 100 e 50000 metros.")
    
    try:
        # Step 1: Buscar lista de XIDs no raio
        radius_endpoint = f"{OPENTRIPMAP_BASE_URL}/0.1/en/places/radius"
        radius_params = {
            "apikey": OPENTRIPMAP_API_KEY,
            "lat": latitude,
            "lon": longitude,
            "radius": radius,
        }
        
        if kinds:
            radius_params["kinds"] = kinds
        
        with httpx.Client() as client:
            radius_response = client.get(radius_endpoint, params=radius_params, timeout=10.0)
            radius_response.raise_for_status()
            
            radius_data = radius_response.json()
        
        # Extrair lista de XIDs
        xids = [item["xid"] for item in radius_data.get("features", [])]
        
        if not xids:
            return {
                "success": True,
                "count": 0,
                "pois": [],
                "message": f"Nenhum POI encontrado no raio de {radius}m em ({latitude}, {longitude})"
            }
        
        # Step 2: Coletar detalhes de cada XID
        pois = []
        
        with httpx.Client() as client:
            for xid in xids:
                try:
                    detail_endpoint = f"{OPENTRIPMAP_BASE_URL}/0.1/en/places/xid/{xid}"
                    detail_params = {"apikey": OPENTRIPMAP_API_KEY}
                    
                    detail_response = client.get(detail_endpoint, params=detail_params, timeout=10.0)
                    detail_response.raise_for_status()
                    
                    detail_data = detail_response.json()
                    
                    # Normalizar dados
                    description = detail_data.get("wikipedia_extracts", {}).get("text", "")
                    if not description:
                        description = detail_data.get("info", {}).get("descr", "")
                    
                    # Truncar descrição para LLM
                    if len(description) > MAX_DESCRIPTION_LENGTH:
                        description = description[:MAX_DESCRIPTION_LENGTH] + "..."
                    
                    poi = {
                        "xid": xid,
                        "name": detail_data.get("name", "Sem nome"),
                        "kinds": detail_data.get("kinds", ""),
                        "description": description,
                        "feature_class": detail_data.get("wikidata", ""),
                        "preview": {
                            "source": detail_data.get("image", {}).get("source", ""),
                            "picture": detail_data.get("image", {}).get("picture", "")
                        },
                        "rate": detail_data.get("rate", "N/A"),
                        "osm_url": detail_data.get("osm_url", "")
                    }
                    
                    pois.append(poi)
                
                except httpx.HTTPStatusError as e:
                    # Log individual errors mas continue processando outros XIDs
                    print(f"Erro ao buscar detalhes do XID {xid}: {e.status_code}")
                    continue
                except Exception as e:
                    print(f"Erro inesperado ao processar XID {xid}: {str(e)}")
                    continue
        
        return {
            "success": True,
            "count": len(pois),
            "pois": pois
        }
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise ToolError(f"Autenticação falhou. Verifique sua OPENTRIPMAP_API_KEY.")
        elif e.response.status_code == 404:
            raise ToolError(f"Nenhum POI encontrado para as coordenadas fornecidas.")
        elif e.response.status_code == 429:
            raise ToolError(f"Rate limit excedido. Aguarde alguns segundos e tente novamente.")
        else:
            raise ToolError(f"Erro na API OpenTripMap (HTTP {e.response.status_code}): {e.response.text}")
    
    except httpx.RequestError as e:
        raise ToolError(f"Erro de conexão com OpenTripMap: {str(e)}")
    
    except ValueError as e:
        raise ToolError(f"Erro ao parsear resposta JSON: {str(e)}")
    
    except Exception as e:
        raise ToolError(f"Erro inesperado: {str(e)}")


if __name__ == "__main__":
    # Executar servidor MCP
    mcp.run()

