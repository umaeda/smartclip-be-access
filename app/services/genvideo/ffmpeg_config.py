import os
import sys
import subprocess
import shutil
import logging

logger = logging.getLogger("smartclip")

def setup_ffmpeg():
    """Configura o ffmpeg e ffprobe no ambiente Heroku"""
    ffmpeg_paths = [
        "/app/vendor/ffmpeg/bin/ffmpeg",  # Caminho do buildpack ffmpeg-latest
        "/usr/bin/ffmpeg",               # Caminho padrão em sistemas Linux
        "/app/.apt/usr/bin/ffmpeg"       # Caminho do buildpack apt
    ]
    
    ffprobe_paths = [
        "/app/vendor/ffmpeg/bin/ffprobe", # Caminho do buildpack ffmpeg-latest
        "/usr/bin/ffprobe",              # Caminho padrão em sistemas Linux
        "/app/.apt/usr/bin/ffprobe"      # Caminho do buildpack apt
    ]
    
    # Verificar caminhos do ffmpeg
    ffmpeg_path = None
    for path in ffmpeg_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            ffmpeg_path = path
            logger.info(f"ffmpeg encontrado em: {ffmpeg_path}")
            break
    
    # Verificar caminhos do ffprobe
    ffprobe_path = None
    for path in ffprobe_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            ffprobe_path = path
            logger.info(f"ffprobe encontrado em: {ffprobe_path}")
            break
    
    # Se não encontrou nos caminhos específicos, tenta encontrar no PATH
    if not ffmpeg_path:
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            logger.info(f"ffmpeg encontrado no PATH: {ffmpeg_path}")
        else:
            logger.warning("ffmpeg não encontrado no sistema!")
    
    if not ffprobe_path:
        ffprobe_path = shutil.which('ffprobe')
        if ffprobe_path:
            logger.info(f"ffprobe encontrado no PATH: {ffprobe_path}")
        else:
            logger.warning("ffprobe não encontrado no sistema!")
    
    # Configurar variáveis de ambiente
    if ffmpeg_path:
        os.environ['FFMPEG_PATH'] = ffmpeg_path
        logger.info(f"Variável de ambiente FFMPEG_PATH configurada: {ffmpeg_path}")
    
    if ffprobe_path:
        os.environ['FFPROBE_PATH'] = ffprobe_path
        logger.info(f"Variável de ambiente FFPROBE_PATH configurada: {ffprobe_path}")
    
    return ffmpeg_path, ffprobe_path

def test_ffmpeg():
    """Testa se o ffmpeg está funcionando corretamente"""
    ffmpeg_path = os.environ.get('FFMPEG_PATH')
    if not ffmpeg_path or not os.path.exists(ffmpeg_path):
        logger.error(f"FFMPEG_PATH inválido: {ffmpeg_path}")
        return False
    
    try:
        # Executar ffmpeg -version para verificar se está funcionando
        result = subprocess.run([ffmpeg_path, "-version"], 
                               capture_output=True, 
                               text=True, 
                               check=True)
        logger.info(f"ffmpeg versão: {result.stdout.splitlines()[0]}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao executar ffmpeg: {e}")
        logger.error(f"Saída de erro: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Erro desconhecido ao testar ffmpeg: {e}")
        return False