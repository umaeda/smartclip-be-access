api_key="EHWVAtZGgcrmjmJamNvYdbdi7OpeuPLVfMMTs7xlCJlxchiUe07FJQQJ99ALACHYHv6XJ3w3AAAYACOGGvb0"
endpoint="https://eastus2.api.cognitive.microsoft.com/"
endpoint = f"https://eastus2.tts.speech.microsoft.com/cognitiveservices/v1"

import requests

# Informações do Azure
#api_key = key
region = "sua-regiao"  # Exemplo: "brazilsouth"
#endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

# Texto que será convertido
text = "Olá, este é um exemplo de texto convertido em fala com Azure."

# Cabeçalhos para a API
headers = {
    "Ocp-Apim-Subscription-Key": api_key,
    "Content-Type": "application/ssml+xml",
    "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3"
}

# Corpo da requisição (SSML)
body = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
       xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="pt-BR">
    <voice name="pt-BR-JulioNeural">
        {text}
    </voice>
</speak>
"""

body = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
       xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="pt-BR">
    <voice name="pt-BR-JulioNeural">
        <mstts:express-as style="empathetic">
            <prosody rate="1.1" pitch="0%">
                Você já ouviu falar em O Livro dos Espíritos? Publicado em 1857, por Allan Kardec, esse é o marco inicial do espiritismo. Um livro revolucionário que traz respostas para as maiores perguntas da humanidade:
De onde viemos? Por que estamos aqui? Para onde vamos?

Com mais de 1000 perguntas e respostas, Kardec organizou ensinamentos dos espíritos sobre a imortalidade da alma, a natureza de Deus, a justiça divina e o sentido da vida.
As lições nos convidam a refletir sobre amor, evolução e a nossa conexão com o universo.

Independente da sua crença, O Livro dos Espíritos nos inspira a buscar conhecimento e a nos tornarmos pessoas melhores.

E você, já leu? Qual pergunta mais te marcou?? Deixe nos comentários!!!
            </prosody>
        </mstts:express-as>
    </voice>
</speak>
"""

# Fazer a requisição para o Azure
response = requests.post(endpoint, headers=headers, data=body)

# Salvar o áudio como MP3
if response.status_code == 200:
    with open("output.mp3", "wb") as audio_file:
        audio_file.write(response.content)
    print("Arquivo MP3 gerado com sucesso!")
else:
    print(f"Erro: {response.status_code}, {response.text}")
