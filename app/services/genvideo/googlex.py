import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Nome do arquivo onde as credenciais serão salvas
TOKEN_PATH = "token.json"

# Escopo de permissões do YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']


def get_credentials():
    credentials = None

    # Se o arquivo token.json já existe, carregamos as credenciais salvas
    if os.path.exists(TOKEN_PATH):
        credentials = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Se não houver credenciais válidas, iniciar o fluxo de autenticação
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            # Se o token expirou, tenta renová-lo automaticamente
            credentials.refresh(Request())
        else:
            # Se não há credenciais, iniciar o fluxo de autenticação
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES
            )
            credentials = flow.run_local_server(port=8080)

            # Salvar credenciais para reutilização futura
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(credentials.to_json())

    return credentials


# Obter as credenciais (reutiliza se já existir token.json)
credentials = get_credentials()

# Criar o serviço do YouTube com as credenciais
youtube = build('youtube', 'v3', credentials=credentials)

print("Autenticação realizada com sucesso!")
