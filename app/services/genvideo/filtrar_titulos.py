import json

# Abrir e carregar o arquivo JSON
with open("dados.json", "r", encoding="utf-8") as arquivo:
    dados = json.load(arquivo)

# Filtrar e imprimir apenas os títulos
for item in dados:
    titulo = item.get("titulo")
    if titulo:
        print(titulo)
