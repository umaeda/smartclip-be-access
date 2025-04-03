# Sistema de Automação de Posts em Redes Sociais com Agentes de IA
# Requerimentos: pip install openai requests moviepy gtts google-api-python-client
import json
import math
from datetime import datetime
import uuid
from . import save_data
import sys
import os

# Fix Python path resolution (modified)
import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# Core imports
from core.social_post import SistemaPostsAutomaticos
from models.post_data import PostData
from .ag_editor_audio import EditorAudio
from .gerador_texto import GeradorTexto
from .ag_gerador_imagem import GeradorImagens
from .gerador_narracao import GeradorNarracao
from .ag_editor_video import EditorVideo
from . import config
import os

# Configuração do ambiente
os.environ["IMAGEMAGICK_BINARY"] = config.IMAGEMAGICK_BINARY

if __name__ == "__main__":
    sistema = SistemaPostsAutomaticos(
        gerador_texto=GeradorTexto(),
        gerador_imagens=GeradorImagens(),
        gerador_narracao=GeradorNarracao(),
        editor_video=EditorVideo(1080, 720),
        editor_audio=EditorAudio()
    )
    
    tema = ("Fenix! Renasça das cinzas e viva!")

    duracao = 35
    qtd_imgs = math.ceil(duracao / 10)
    
    sistema.executar_fluxo(tema=tema, modelo='gemini', 
                         duracao=duracao, qtd_imagens=qtd_imgs)

