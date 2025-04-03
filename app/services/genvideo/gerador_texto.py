import json
import math
import re
from langchain_community.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

# --- Agente de Geração de Texto ---
class GeradorTexto:
    @staticmethod

    def gerar_roteiro(tema=None, modelo='gemini', duracao=30, qtd_imagens=1):
        """
        Gera um roteiro para um Short de duração especificada sobre o tema escolhido.

        :param tema: O tema do roteiro
        :param modelo: O modelo de IA a ser utilizado ('openai', 'gemini')
        :param duracao: Tempo máximo de leitura do texto (segundos)
        :return: Dicionário JSON com título, texto e hashtags
        """

        prompt = f"""Crie um texto para ser lido em um Short evitando usar call to action.
        Tema: {tema}
        - Deve ter Introdução impactante, um rápido desenvolvimento e Chamada para ação.
        - gere tambem {qtd_imagens} frases sobre o tema introducao, ponto principal e chamada para acao.
        A leitura não deve levar mais que {duracao} segundos e deve ter quebra de linhas para colocar como legenda no formato de shorts.
        Acrecente tambem uma legenda para o post. 
        Deve possuir apenas texto e pontuação bem marcante para facilitar a narracao, 
        sem marcações da narração e formatação de fonte e sem emojis.
        O resultado deve ser um JSON válido no formato:
        {{
          "titulo": "Título do Vídeo",
          "texto": "Texto para narração",
          "frases": "['frase1','frase2']" 
          "hashtag": "#tag1 #tag2",
          "legenda"; "legenda para o post"
        }}
        Retorne apenas o JSON, sem explicações adicionais.
        """

        # Escolha do modelo de IA
        if modelo == 'openai':
            chat = ChatOpenAI(model_name="gpt-4", temperature=0.7)
        elif modelo == 'gemini':
            chat = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.7)
        else:
            raise ValueError("Modelo não suportado. Escolha entre 'openai' ou 'gemini'.")

        # Gera a resposta do modelo
        response = chat.invoke([HumanMessage(content=prompt)])

        # Converte a resposta para string
        response_text = response.content if hasattr(response, "content") else str(response)

        # Extração segura de JSON
        json_data = GeradorTexto.extrair_json(response_text)

        return json_data

    @staticmethod
    def extrair_json(texto):
        """
        Extrai um JSON válido de um texto gerado pelo modelo de IA.
        :param texto: Resposta do modelo contendo um JSON
        :return: Dicionário JSON validado
        """
        try:
            # Regex para encontrar um JSON dentro da resposta
            json_match = re.search(r'\{.*\}', texto, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)  # Extrai apenas o JSON encontrado
                return json.loads(json_str)  # Converte para dicionário
            else:
                raise ValueError("Nenhum JSON válido encontrado na resposta.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Erro ao converter resposta em JSON: {str(e)}")

    @staticmethod
    def gerar_prompt_frase(tema=None, frase=None, modelo='gemini'):
        """
        Gera um roteiro para um Short de duração especificada sobre o tema escolhido.

        :param tema: O tema do roteiro
        :param modelo: O modelo de IA a ser utilizado ('openai', 'gemini')
        :param duracao: Tempo máximo de leitura do texto (segundos)
        :return: Dicionário JSON com título, texto e hashtags
        """

        prompt = f"""Crie um um prompt de entrada para gerar imagem..
        Tema: {tema}
        frase que irá basear a imagem dentro do tema é :{frase}
        retorne apenas a descricao de como deve ser a imagem em texto corrido
        """

        # Escolha do modelo de IA
        if modelo == 'openai':
            chat = ChatOpenAI(model_name="gpt-4", temperature=0.7)
        elif modelo == 'gemini':
            chat = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0.7)
        else:
            raise ValueError("Modelo não suportado. Escolha entre 'openai' ou 'gemini'.")

        # Gera a resposta do modelo
        response = chat.invoke([HumanMessage(content=prompt)])

        # Converte a resposta para string
        response_text = response.content if hasattr(response, "content") else str(response)

        return response_text

    @staticmethod
    def gerar_promt_frases_imagem(texto, raw_frases):
        frases = []
        for frase in raw_frases:
            prompt_frase = GeradorTexto.gerar_prompt_frase(texto, frase)
            frases.append(prompt_frase)

        return frases

    @staticmethod
    def texto_para_ssml(texto, modelo='gemini'):
        prompt = f"""Utilizes as orientacoes para dar enfase em frases colocando as marcacoes ssml e removendo o conteudo desnecessario.
                coloque tags como break time e emphasis para dar maior fluidez no texto conforme orientado.
                remova as marcacoes desnecessarias (20 segundos de introducao) por exemplo.
                Os break time podem ter no maximo 400ms
                use <prosody rate="1.05" pitch="-3%">
                <voice name="pt-BR-AntonioNeural">
                nao cololque breaktime apos os ... (3 pontos)
                retorne apenas o conteudo xml sem explicacoes.
                não precisa incluir o ```xml e ``` no final. 
                texto a ser convertido: {texto}
                
                o resultado esperado é: 
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
                       xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="pt-BR">
                    <voice name="pt-BR-FabioNeural">
                        <mstts:express-as style="narration-professional">
                            <prosody rate="1.0" pitch="-6%">
                               <s>Que a paz de Jesus Cristo, <break time="300ms"/></s>
                               <s>Às vezes, <emphasis level="moderate">ser mais caridoso</emphasis> não exige grandes esforços.</s>
                            </prosody>
                        </mstts:express-as>
                    </voice>
                </speak>
        """
        # Escolha do modelo de IA
        if modelo == 'openai':
            chat = ChatOpenAI(model_name="gpt-4", temperature=0.1)
        elif modelo == 'gemini':
            chat = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0.1)
        else:
            raise ValueError("Modelo não suportado. Escolha entre 'openai' ou 'gemini'.")

        # Gera a resposta do modelo
        response = chat.invoke([HumanMessage(content=prompt)])

        # Converte a resposta para string
        response_text = response.content if hasattr(response, "content") else str(response)

        return response_text

