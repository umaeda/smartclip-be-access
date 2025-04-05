import uuid
import os
import json
from datetime import datetime
from typing import Dict, Any, List

def mock_video_data(titulo: str, duracao_segundos: int) -> Dict[str, Any]:
    """
    Gera dados simulados (mock) para um vídeo.
    Útil para testes e desenvolvimento sem depender da geração real de vídeos.
    
    Args:
        titulo: Título/tema do vídeo
        duracao_segundos: Duração desejada do vídeo em segundos
        
    Returns:
        Dict[str, Any]: Dicionário com informações simuladas do vídeo
    """
    # Gera um identificador único
    identificador = str(uuid.uuid4())
    
    # Simula o tempo de geração (entre 10 e 30 segundos por cada 10 segundos de vídeo)
    generation_time = duracao_segundos * 2.5
    
    # Caminhos simulados para arquivos
    base_path = os.path.join(os.getcwd(), "mock_files")
    video_filename = f"video_{identificador[:8]}.mp4"
    audio_raw_filename = f"audio_raw_{identificador[:8]}.mp3"
    audio_remix_filename = f"audio_remix_{identificador[:8]}.mp3"
    
    # Simula caminhos de arquivos
    arquivo_video = "C:\\projetos\\python\\redesocial\\2fba7034-7116-4a4a-babf-c83ac85bfc89.mp4"
    arquivo_narracao_raw = os.path.join(base_path, audio_raw_filename)
    arquivo_narracao_remix = os.path.join(base_path, audio_remix_filename)
    
    # Simula um roteiro baseado no título
    roteiro = f"""# {titulo.upper()}

Olá pessoal! Hoje vamos falar sobre {titulo}.

Você sabia que {titulo} é um dos assuntos mais interessantes da atualidade?

Vamos explorar alguns pontos importantes sobre este tema fascinante.

Primeiro, é importante entender o contexto histórico de {titulo}.

Em seguida, vamos analisar o impacto de {titulo} na sociedade moderna.

Por fim, vamos discutir o futuro de {titulo} e suas implicações.

Espero que tenham gostado deste conteúdo! Não se esqueça de curtir e compartilhar."""
    
    # Simula frases para geração de imagens
    frases = [
        f"Uma ilustração moderna sobre {titulo}",
        f"Pessoas interagindo com {titulo} em um ambiente urbano",
        f"Gráfico mostrando o crescimento de {titulo} nos últimos anos",
        f"Representação artística do conceito de {titulo}",
        f"Futuro de {titulo} representado em estilo futurista"
    ]
    
    # Simula hashtags
    hashtags = f"#SmartClip #{titulo.replace(' ', '')} #ConteudoDigital #VideoAutomatico #IA"
    
    # Simula conteúdo/legenda
    conteudo = f"""🎬 {titulo.upper()} 🎬

Descubra tudo sobre {titulo} neste vídeo incrível gerado com SmartClip!

Comentários? Deixe abaixo! 👇

{hashtags}"""
    
    # Simula caminhos de imagens
    imagens = [
        os.path.join(base_path, f"imagem_{i}_{identificador[:8]}.jpg") 
        for i in range(1, 3)
    ]
    
    # Simula narração marcada com SSML
    narracao_marcada = f"""<speak>
    <p>Olá pessoal! Hoje vamos falar sobre {titulo}.</p>
    <break time='500ms'/>
    <p>Você sabia que {titulo} é um dos assuntos mais interessantes da atualidade?</p>
    <break time='500ms'/>
    <p>Vamos explorar alguns pontos importantes sobre este tema fascinante.</p>
    <break time='1s'/>
    <p>Primeiro, é importante entender o contexto histórico de {titulo}.</p>
    <break time='500ms'/>
    <p>Em seguida, vamos analisar o impacto de {titulo} na sociedade moderna.</p>
    <break time='500ms'/>
    <p>Por fim, vamos discutir o futuro de {titulo} e suas implicações.</p>
    <break time='1s'/>
    <p>Espero que tenham gostado deste conteúdo! Não se esqueça de curtir e compartilhar.</p>
</speak>"""
    
    # Cria o objeto post_data simulado
    post_data = {
        "guid": identificador,
        "solicitacao": titulo,
        "titulo": titulo,
        "roteiro": roteiro,
        "frases": frases,
        "hashtags": hashtags,
        "conteudo": conteudo,
        "imagens": imagens,
        "narracao_marcada": narracao_marcada,
        "arquivo_narracao_raw": arquivo_narracao_raw,
        "arquivo_narracao_remix": arquivo_narracao_remix,
        "arquivo_video": arquivo_video,
        "data_registro": datetime.now().isoformat()
    }
    
    # Retorna o resultado simulado
    return {
        "url": arquivo_video,
        "duration": duracao_segundos,
        "generation_time": generation_time,
        "post_data": post_data
    }