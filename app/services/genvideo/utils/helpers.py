import json

def carregar_registro_por_guid(guid: str) -> dict:
    """Carrega um registro do arquivo dados.json pelo GUID"""
    with open('dados.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if registro := next((item for item in data if item.get('guid') == guid), None):
        return registro
    raise ValueError(f"Nenhum registro encontrado para o GUID: {guid}")