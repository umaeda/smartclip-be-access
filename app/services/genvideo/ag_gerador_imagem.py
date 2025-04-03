import os
import random
import string

from PIL import Image
import requests
import time
import base64
import math



# --- Agente de Geração de Imagens ---
class GeradorImagens:

    def __init__(self):
        None

    def criar_imagens(self, tema, frases, identificador=""):
        picker = FreepikImageGenerator()
        caminhos_imagens = []

        for frase in frases:
            assunto = f"{frase}.  -prefira usar fotos de objetos e lugares"
            img_url = picker.gerar_imagem(tema=assunto, identificador=identificador)
            caminhos_imagens.append(img_url)

        return caminhos_imagens

        #return ['c:/projetos/python/redesocial/1.png','c:/projetos/python/redesocial/2.png','c:/projetos/python/redesocial/3.png']


    # def criar_imagens(self, texto, duracao):
    #     """
    #     Recupera imagens de uma pasta pré-determinada no formato WEBP, converte para PNG
    #     e retorna os caminhos dos arquivos convertidos.
    #
    #     Parâmetros:
    #         texto: (não utilizado neste método) pode ser o prompt para geração de imagens.
    #         num_imagens: Número de imagens a serem recuperadas (padrão: 3).
    #
    #     Retorna:
    #         Uma lista de caminhos dos arquivos PNG convertidos.
    #     """
    #
    #
    #     # Caminho da pasta pré-determinada contendo as imagens no formato WEBP
    #     pasta_imagens = "c:/projetos/python/redesocial/imagens"
    #
    #     # Lista todos os arquivos com extensão .webp (case insensitive)
    #     arquivos_webp = [os.path.join(pasta_imagens, f)
    #                      for f in os.listdir(pasta_imagens)
    #                      if f.lower().endswith(".webp")]
    #
    #     # Seleciona os primeiros num_imagens (você pode alterar para selecionar aleatoriamente, se desejar)
    #     arquivos_selecionados = sorted(arquivos_webp)[:num_imagens]
    #
    #     arquivos_convertidos = []
    #     for arquivo in arquivos_selecionados:
    #         # Abre a imagem WEBP
    #         img = Image.open(arquivo)
    #         # Converte para RGB se necessário
    #         if img.mode != "RGB":
    #             img = img.convert("RGB")
    #         # Define o caminho de saída, mantendo o mesmo nome e substituindo a extensão para .png
    #         arquivo_saida = arquivo.rsplit(".", 1)[0] + ".png"
    #         # Salva a imagem no formato PNG
    #         img.save(arquivo_saida, "PNG")
    #         arquivos_convertidos.append(arquivo_saida)
    #
    #     return arquivos_convertidos



import requests
import os

class FreepikImageGenerator:
    API_KEY = "FPSX7eb3b2008f1d4ab890da7b3589cb9c95"  # Substitua pela sua chave de API do Freepik
    API_URL = "https://api.freepik.com/v1/ai/text-to-image"

    def gerar_imagem(self,
                     tema,
                     modelo="",#"/classic-fast-mode",
                     tamanho="square", #widescreen_16_9 #"social_story_9_16", #square
                     num_imagens=1,
                     negative_prompt="camera",
                     guidance_scale=1,
                     seed=random.randint(0, 1000000),
                     estilo="photo", #photo 3d
                     cor="dramatic", #pastel vibrant
                     iluminacao="cinematic", #lavender dramatic warm
                     enquadramento="cinematic", #portrait
                     pasta_destino="./imagens/",
                     identificador=""
                     ):
        """
        Gera uma imagem baseada no texto usando a API do Freepik AI.

        :param texto: Texto para gerar a imagem (prompt)
        :param modelo: Modelo da IA (exemplo: "classic-fast-mode")
        :param tamanho: Tamanho da imagem (exemplo: "square", "portrait", "landscape")
        :param num_imagens: Número de imagens a serem geradas
        :param negative_prompt: Elementos para evitar na imagem
        :param guidance_scale: Nível de orientação da IA (quanto maior, mais fiel ao prompt)
        :param seed: Semente aleatória para reprodutibilidade
        :param estilo: Estilo da imagem (exemplo: "anime", "photorealistic")
        :param cor: Paleta de cores (exemplo: "pastel", "vibrant")
        :param iluminacao: Tipo de iluminação (exemplo: "warm", "cold")
        :param enquadramento: Tipo de enquadramento (exemplo: "portrait", "landscape")
        :return: Lista de URLs das imagens geradas ou None se falhar
        """
        headers = {
            "x-freepik-api-key": self.API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": tema,
            "negative_prompt": negative_prompt,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "num_images": num_imagens,
            "image": {
                "size": tamanho
            },
            "styling": {
                "style": estilo,
                "color": cor,
                "lightning": iluminacao,
                "framing": enquadramento
            }
        }

        try:
            response = requests.post(f"{self.API_URL}{modelo}", json=payload, headers=headers, verify=False)

            if response.status_code == 200:
                data = response.json()
                imagens_base64 = [img["base64"] for img in data.get("data", [])]  # Extrai Base64

                return self.salvar_imagens(imagens_base64=imagens_base64, pasta_destino=pasta_destino, identificador=identificador)

            else:
                print(f"Erro ao gerar imagem: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            print(f"Erro de conexão com a API: {str(e)}")
            return None

    def salvar_imagens(self, imagens_base64, pasta_destino, identificador=""):
        """
        Salva imagens decodificadas de Base64 para arquivos locais.

        :param imagens_base64: Lista de strings Base64 das imagens
        :param pasta_destino: Diretório onde as imagens serão salvas
        :return: Lista de caminhos dos arquivos salvos
        """
        if not imagens_base64:
            print("Nenhuma imagem em Base64 fornecida.")
            return None

        # Criar a pasta se não existir
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        caminho_imagem = ""

        #caminhos_imagens = []
        for i, img_base64 in enumerate(imagens_base64):
            caminho_imagem = os.path.join(pasta_destino, f"{identificador}_{self.gerar_alphanumerico_aleatorio()}.png")

            # Decodifica a imagem Base64 e salva
            try:
                with open(caminho_imagem, "wb") as file:
                    file.write(base64.b64decode(img_base64))
                #caminhos_imagens.append(caminho_imagem)
                print(f"Imagem salva em: {caminho_imagem}")
            except Exception as e:
                print(f"Erro ao salvar a imagem {i + 1}: {str(e)}")

        return caminho_imagem


    def gerar_alphanumerico_aleatorio(self,tamanho=6):
        caracteres = string.ascii_letters + string.digits  # Letras (maiúsculas e minúsculas) e dígitos
        return ''.join(random.choices(caracteres, k=tamanho))