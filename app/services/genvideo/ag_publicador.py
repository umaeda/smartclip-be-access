
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class PublicadorTikTok:
    #def __init__(self, client_secret='a1YOVU2csT3gSfQ8Qk4arYmuejAf3nLJ', client_key='awmdwvq3685rsw3u'):
    def __init__(self, client_secret='PZ5Ae9KUs4NHWTyK3pGAC7GMdpQoCjH1', client_key='sbaw0vpcr1a5tofa92'): #sandbox
        """
        Inicializa o publicador para TikTok.

        Parâmetros:
            access_token: Token de acesso obtido via OAuth.
            client_key: Chave do cliente (client key) fornecida pelo TikTok.
        """
        self.base_url = "https://open.tiktokapis.com"
        #self.base_url = "https://sandbox-ads.tiktok.com"
        self.client_secret = client_secret
        self.client_key = client_key
        self.access_token =  self.obter_access_token()
        print(self.access_token)

    def obter_access_token(self):
        """
        Recupera o token de acesso do TikTok via OAuth.

        Retorna:
            dict: Resposta da API contendo o token de acesso ou mensagem de erro.
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache"
        }

        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        self.token_url = f"{self.base_url}/v2/oauth/token/"

        response = requests.post(self.token_url, headers=headers, data=data)

        if response.status_code == 200:
            token_info = response.json()
            print("✅ Token obtido com sucesso!")
            return token_info['access_token']
        else:
            print(f"❌ Erro ao obter token: {response.status_code} - {response.text}")
            return response.json()



    def verificar_elegibilidade(self):
        """
        Verifica se a conta está autorizada a publicar via API.

        Retorna:
            True se a conta pode postar, False caso contrário.
        """

        url = f"{self.base_url}/v2/post/publish/creator_info/query/"
        headers = {"Authorization": f"Bearer {self.access_token}",
                   "content-Type": "application/json"}

        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("is_eligible_for_posting", False)
        else:
            print(f"Erro ao verificar conta: {response.status_code} - {response.text}")
            return False

    def publicar_video(self, arquivo, caption):
        """
        Publica o vídeo no TikTok seguindo as etapas da API oficial.

        Parâmetros:
            arquivo: Caminho para o arquivo de vídeo.
            caption: Legenda ou descrição para o vídeo.

        Retorna:
            A resposta JSON da API.
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # 1️⃣ **Verificar se a conta está habilitada para postar**
        if not self.verificar_elegibilidade():
            return {"error": "Conta não habilitada para postagens via API."}

        try:
            # 2️⃣ **Inicializar o Upload**
            init_url = f"{self.base_url}/v2/post/publish/inbox/video/init/"
            init_payload = {
                "source_info": {"source": "FILE_UPLOAD"}
            }
            init_response = requests.post(init_url, json=init_payload, headers=headers)

            if init_response.status_code != 200:
                print(f"Erro ao inicializar upload: {init_response.status_code}, {init_response.text}")
                return init_response.json()

            upload_info = init_response.json()
            upload_url = upload_info.get("upload_url")
            video_id = upload_info.get("video_id")

            if not upload_url or not video_id:
                return {"error": "Não foi possível obter URL de upload."}

            print("✅ Upload inicializado. Enviando vídeo...")

            # 3️⃣ **Enviar o vídeo**
            with open(arquivo, "rb") as video_file:
                upload_headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "video/mp4"
                }
                upload_response = requests.put(upload_url, headers=upload_headers, data=video_file)

            if upload_response.status_code != 200:
                print(f"Erro ao enviar vídeo: {upload_response.status_code}, {upload_response.text}")
                return upload_response.json()

            print("✅ Vídeo enviado. Finalizando publicação...")

            # 4️⃣ **Finalizar e Publicar**
            commit_url = f"{self.base_url}/v2/post/publish/inbox/video/commit/"
            commit_payload = {
                "video_id": video_id,
                "post_info": {"title": caption}
            }
            commit_response = requests.post(commit_url, json=commit_payload, headers=headers)

            if commit_response.status_code == 200:
                print("🎉 Vídeo publicado com sucesso no TikTok!")
                return commit_response.json()
            else:
                print(f"Erro ao finalizar upload: {commit_response.status_code}, {commit_response.text}")
                return commit_response.json()

        except Exception as e:
            print(f"Erro inesperado: {e}")
            return {"error": str(e)}


# --- Agente de Publicação via Simplified ---
class PublicadorSimplified:
    def __init__(self, api_key):
        self.api_key = api_key
        # Endpoint fictício – ajuste conforme a documentação real do Simplified
        self.base_url = "https://api.simplified.com/v1"

    def publicar_video(self, arquivo, caption, platforms):
        """
        Publica o vídeo em múltiplas plataformas (Instagram, TikTok, YouTube)
        usando a API do Simplified.

        Parâmetros:
            arquivo: Caminho para o arquivo de vídeo.
            caption: Legenda ou descrição do post.
            platforms: Lista de plataformas (ex: ["instagram", "tiktok", "youtube"]).

        Retorna:
            A resposta da API (JSON).
        """
        url = f"{self.base_url}/posts"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "caption": caption,
            "platforms": platforms
        }
        files = {
            "media": open(arquivo, "rb")
        }
        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            print("Vídeo publicado com sucesso no Simplified!")
        else:
            print(f"Erro ao publicar: {response.status_code}, {response.text}")
        return response.json()

# --- Agente de Publicação ---
import os
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Caminho do arquivo onde as credenciais são armazenadas
TOKEN_PATH = "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class PublicadorYoutube:
    def __init__(self):
        self.credentials = self.get_credentials()
        self.youtube = build("youtube", "v3", credentials=self.credentials)

    def get_credentials(self):
        """Obtém as credenciais do arquivo salvo ou inicia um novo fluxo de autenticação."""
        credentials = None

        if os.path.exists(TOKEN_PATH):
            credentials = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())  # Atualiza automaticamente o token expirado
            else:
                raise Exception("Credenciais inválidas. Execute a autenticação novamente.")

        return credentials

    def upload_youtube_short(self, video_path, title, description, category_id="22", privacy_status="public"):
        """
        Faz upload de um vídeo no YouTube como um Short.

        Parâmetros:
            video_path (str): Caminho do arquivo de vídeo.
            title (str): Título do vídeo.
            description (str): Descrição do vídeo.
            category_id (str): ID da categoria do vídeo (default: "22" - Entretenimento).
            privacy_status (str): Status de privacidade do vídeo ("public", "private" ou "unlisted").

        Retorna:
            dict: Resposta da API do YouTube.
        """
        # Metadados do vídeo
        request_body = {
            "snippet": {
                "title": title,
                "description": description + " #Shorts",  # Adiciona #Shorts para melhorar o alcance
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }

        # Upload do vídeo
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )

        response = request.execute()
        print("✅ Upload concluído! Vídeo ID:", response["id"])
        return response
