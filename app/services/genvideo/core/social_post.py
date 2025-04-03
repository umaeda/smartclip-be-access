from datetime import datetime
import uuid
import os
import math

from app.services.genvideo import save_data
# Importações corretas com caminho completo
from app.services.genvideo.models.post_data import PostData
from app.services.genvideo.utils.helpers import carregar_registro_por_guid

class SistemaPostsAutomaticos:
    def __init__(self, gerador_texto, gerador_imagens, gerador_narracao, editor_video, editor_audio):
        self.gerador_texto = gerador_texto
        self.gerador_imagens = gerador_imagens
        self.gerador_narracao = gerador_narracao
        self.editor_video = editor_video
        self.editor_audio = editor_audio

    def executar_fluxo(self, tema, modelo, duracao, qtd_imagens):
        identificador = str(uuid.uuid4())

        # 1. Geração de conteúdo
        data_post = self.gerador_texto.gerar_roteiro(tema=tema, modelo=modelo, duracao=duracao, qtd_imagens=qtd_imagens)
        roteiro = data_post.get("texto", "Sem título")
        titulo = data_post.get("titulo", "Sem título")
        raw_frases = data_post.get("frases", "Sem título")
        hashtags = data_post.get("hashtag", "#default")
        conteudo = data_post.get("legenda", "#default")

        frases = self.gerador_texto.gerar_promt_frases_imagem(roteiro, raw_frases)

        print(titulo)
        print(f"Roteiro gerado:\n{roteiro}\n")
        print(f"frases:  {frases}\n")
        print(f"hashtags:  {hashtags}\n")
        print(f"conteudo:  {conteudo}\n")
        print(f"titulo:  {titulo}\n")
        # 2. Produção de audio
        texto_para_audio_ssml = self.gerador_texto.texto_para_ssml(roteiro)
        narracao_raw = self.gerador_narracao.texto_para_audio_ssml(texto_para_audio_ssml, f"{identificador}")
        narracao_remix = self.editor_audio.remixar_estilo_reflexao(narracao_raw, identificador=identificador)

        # 3. Produção de Imagems e Video
        imagens = self.gerador_imagens.criar_imagens(tema=tema, frases=frases, identificador=identificador)
        arquivo_video = self.editor_video.criar_animacao(imagens,
                                                         audio_path=narracao_remix,
                                                         transition_duration=3,
                                                         legenda_texto=roteiro,
                                                         titulo=titulo,
                                                         identificador=identificador)

                                                        
        post_data = {
            "guid": identificador,
            "solicitacao": tema,
            "titulo": titulo,
            "roteiro": roteiro,
            "frases": frases,
            "hashtags": hashtags,
            "conteudo": conteudo,
            "imagens": imagens,
            "narracao_marcada": texto_para_audio_ssml,
            "arquivo_narracao_raw": narracao_raw,
            "arquivo_narracao_remix": narracao_remix,
            "arquivo_video": arquivo_video,
            "data_registro": datetime.now().isoformat()
        }
        save_data.append_data_to_json(post_data)

        print(os.path.abspath(arquivo_video))

        return os.path.abspath(arquivo_video)