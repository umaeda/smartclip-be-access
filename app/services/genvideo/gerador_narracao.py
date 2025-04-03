import os

import requests
from .gerador_texto import GeradorTexto
# --- Agente de Narração ---
class GeradorNarracao:
    def __init__(self):
        self.pasta_destino="./narracao/"

    def gera_narrracao(self, texto=None, arquivo_saida='narracao.mp3'):

        texto_para_audio_ssml = GeradorTexto().texto_para_audio_ssml(texto)
        output = self.texto_raw_para_audio(texto_para_audio_ssml, arquivo_saida)
        return output


    def texto_raw_para_audio(self, texto=None, arquivo_saida='narracao.mp3'):

        #return arquivo_saida

        # Dados de autenticação e endpoint do Azure TTS
        api_key = "EHWVAtZGgcrmjmJamNvYdbdi7OpeuPLVfMMTs7xlCJlxchiUe07FJQQJ99ALACHYHv6XJ3w3AAAYACOGGvb0"
        endpoint = "https://eastus2.tts.speech.microsoft.com/cognitiveservices/v1"

        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3"
        }

        # Corpo da requisição (SSML) com o texto a ser convertido
        ssml = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
           xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="pt-BR">
        <voice name="pt-BR-FabioNeural">
            <mstts:express-as style="empathetic">
                <prosody rate="1.05" pitch="-3%">
                    {texto}
                </prosody>
            </mstts:express-as>
        </voice>
    </speak>
    """
        # Faz a requisição para a API do Azure TTS
        response = requests.post(endpoint, headers=headers, data=ssml)

        if not os.path.exists(self.pasta_destino):
            os.makedirs(self.pasta_destino)
        arquivo_saida = os.path.join(self.pasta_destino, f"{arquivo_saida}.mp3")

        if response.status_code == 200:
            with open(arquivo_saida, "wb") as audio_file:
                audio_file.write(response.content)
            print("Arquivo MP3 gerado com sucesso!")
        else:
            print(f"Erro: {response.status_code}, {response.text}")

        return arquivo_saida

    def texto_para_audio2(self, arquivo_saida='narracao3.mp3'):
        #return arquivo_saida
        # Dados de autenticação e endpoint do Azure TTS
        api_key = "EHWVAtZGgcrmjmJamNvYdbdi7OpeuPLVfMMTs7xlCJlxchiUe07FJQQJ99ALACHYHv6XJ3w3AAAYACOGGvb0"
        endpoint = "https://eastus2.tts.speech.microsoft.com/cognitiveservices/v1"

        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3"
        }

        # Corpo da requisição (SSML) com o texto a ser convertido
        ssml = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
   xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="pt-BR">

<voice name="pt-BR-FabioNeural">
    <mstts:express-as style="narration-professional">
        <prosody rate="1.0" pitch="-6%">

            <s>Já parou para pensar... no poder de um simples gesto de bondade?</s>

            <s>Às vezes, <emphasis level="moderate">ser mais caridoso</emphasis> não exige grandes esforços.</s>

            <s>Um sorriso sincero... Uma palavra amiga... Ou apenas <emphasis level="moderate">ouvir</emphasis> alguém que precisa ser ouvido.</s>

            <s>Caridade não é só dar dinheiro. <break time="200ms"/> É dar tempo... atenção... e empatia.</s>

            <s>É enxergar o outro <emphasis level="strong">de verdade</emphasis>.</s>

            <s>Então, hoje... que tal fazer algo por alguém... sem esperar nada em troca?</s>

            <s>Pequenos gestos podem transformar o dia de alguém... e o seu também. <break time="300ms"/></s>

            <s><emphasis level="strong">Seja a mudança.</emphasis></s>

        </prosody>
    </mstts:express-as>
</voice>

</speak>




    """
        # Faz a requisição para a API do Azure TTS
        response = requests.post(endpoint, headers=headers, data=ssml)

        if response.status_code == 200:
            with open(arquivo_saida, "wb") as audio_file:
                audio_file.write(response.content)
            print("Arquivo MP3 gerado com sucesso!")
        else:
            print(f"Erro: {response.status_code}, {response.text}")

        return arquivo_saida

    def texto_para_audio_ssml(self, texto_ssml, identificador):
        # return arquivo_saida
        # Dados de autenticação e endpoint do Azure TTS
        api_key = "EHWVAtZGgcrmjmJamNvYdbdi7OpeuPLVfMMTs7xlCJlxchiUe07FJQQJ99ALACHYHv6XJ3w3AAAYACOGGvb0"
        endpoint = "https://eastus2.tts.speech.microsoft.com/cognitiveservices/v1"

        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3"
        }

        # Corpo da requisição (SSML) com o texto a ser convertido
        ssml = f"""{texto_ssml.replace("```xml", "").replace("```", "").strip()}"""

        # Faz a requisição para a API do Azure TTS
        response = requests.post(endpoint, headers=headers, data=ssml)

        if not os.path.exists(self.pasta_destino):
            os.makedirs(self.pasta_destino)
        arquivo_saida = os.path.join(self.pasta_destino, f"{identificador}.mp3")

        if response.status_code == 200:

            with open(arquivo_saida, "wb") as audio_file:
                audio_file.write(response.content)
            print("Arquivo MP3 gerado com sucesso!")
        else:
            print(f"Erro: {response.status_code}, {response.text}")

        return arquivo_saida

# x = GeradorNarracao()
# x.texto_para_audio_ssml("a", "A.mp3")
