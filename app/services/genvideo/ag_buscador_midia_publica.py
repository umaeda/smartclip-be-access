import requests
import os


class BuscadorMidiaPublica:
    def __init__(self, api_key):
        self.api_key = api_key #"49093742-1a00d51cd6e34465fc7121387"
        self.endpoint_imagens = "https://pixabay.com/api/"
        self.endpoint_videos = "https://pixabay.com/api/videos/"

    def buscar_imagens(self, query, num=3):
        """
        Busca imagens gratuitas no Pixabay com base no query.

        Parâmetros:
            query: Texto de busca.
            num: Número de imagens a retornar.

        Retorna:
            Uma lista de URLs das imagens encontradas.
        """
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": num,
            "safesearch": "true"
        }
        response = requests.get(self.endpoint_imagens, params=params, verify=False)
        if response.status_code == 200:
            data = response.json()
            return [hit["largeImageURL"] for hit in data.get("hits", [])]
        else:
            print("Erro ao buscar imagens:", response.status_code, response.text)
            return []

    def buscar_videos(self, query, num=3):
        """
        Busca vídeos gratuitos no Pixabay com base no query.

        Parâmetros:
            query: Texto de busca.
            num: Número de vídeos a retornar.

        Retorna:
            Uma lista de URLs dos vídeos (utilizando a resolução 'medium').
        """
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": num,
            "safesearch": "true"
        }
        response = requests.get(self.endpoint_videos, params=params, verify=False)
        if response.status_code == 200:
            data = response.json()
            # Retorna a URL da versão 'medium' de cada vídeo
            return [hit["videos"]["medium"]["url"] for hit in data.get("hits", [])]
        else:
            print("Erro ao buscar vídeos:", response.status_code, response.text)
            return []


    def download_imagens(self, urls, pasta_destino):
        """
        Faz o download de imagens a partir de uma lista de URLs e salva na pasta de destino.

        Parâmetros:
            urls: Lista de URLs das imagens.
            pasta_destino: Caminho da pasta onde as imagens serão salvas.
        """
        # Cria a pasta, se ela não existir
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        for url in urls:
            try:
                response = requests.get(url, verify=False)
                response.raise_for_status()  # Levanta uma exceção para códigos de status de erro
                # Extrai o nome do arquivo a partir da URL, removendo parâmetros (query string)
                nome_arquivo = os.path.basename(url.split('?')[0])
                caminho_completo = os.path.join(pasta_destino, nome_arquivo)
                with open(caminho_completo, "wb") as f:
                    f.write(response.content)
                print(f"Imagem salva: {caminho_completo}")
            except requests.RequestException as e:
                print(f"Erro ao baixar a imagem {url}: {e}")