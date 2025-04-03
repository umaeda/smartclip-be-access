import json
import os
from datetime import datetime


def load_data_from_json(filename="dados.json"):
    """
    Carrega todos os dados de um arquivo JSON.
    Se o arquivo não existir ou estiver vazio, retorna uma lista vazia.

    :param filename: Nome do arquivo JSON.
    :return: Lista com todos os dados do arquivo JSON.
    """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]
                return data
            except json.JSONDecodeError:
                return []
    else:
        return []


def append_data_to_json(new_data, filename="dados.json"):
    """
    Adiciona (apenda) os novos dados a um arquivo JSON existente.
    Se o arquivo não existir ou estiver vazio, ele é criado.

    :param new_data: Dados a serem adicionados (por exemplo, um dicionário)
    :param filename: Nome do arquivo JSON.
    """
    # Verifica se o arquivo já existe
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                # Tenta carregar os dados existentes
                data = json.load(f)
                # Se os dados não forem uma lista, os transforma em uma lista
                if not isinstance(data, list):
                    data = [data]
            except json.JSONDecodeError:
                # Caso o arquivo esteja vazio ou com erro, inicia com lista vazia
                data = []
    else:
        data = []

    # Adiciona os novos dados à lista
    data.append(new_data)

    # Escreve de volta para o arquivo, preservando os dados existentes
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Dados adicionados em {filename}")


# Exemplo de uso:
if __name__ == '__main__':
    # Suponha que estas variáveis foram geradas no seu fluxo:
    titulo = "Título Exemplo"
    roteiro = "Este é o roteiro gerado..."
    frases = ["Frase 1", "Frase2"]
    hashtags = "#exemplo #teste"
    conteudo = "Conteúdo para legenda..."

    # Cria um dicionário com os dados do post
    post_data = {
        "titulo": titulo,
        "roteiro": roteiro,
        "frases": frases,
        "hashtags": hashtags,
        "conteudo": conteudo,
        "data_registro": datetime.now().isoformat()
    }

    # Apende os dados no arquivo JSON
    append_data_to_json(post_data, filename="posts.json")
