import os
import sys
import re
import warnings
import logging
from pydub import AudioSegment

# Importar o módulo de configuração do ffmpeg
from app.services.genvideo.ffmpeg_config import setup_ffmpeg, test_ffmpeg

# Configurar logger
logger = logging.getLogger("smartclip")

# Configuração do ffmpeg e ffprobe usando o módulo de configuração
try:
    # Configurar ffmpeg e ffprobe
    ffmpeg_path, ffprobe_path = setup_ffmpeg()
    
    # Configurar pydub para usar os caminhos encontrados
    if ffmpeg_path:
        AudioSegment.converter = ffmpeg_path
        logger.info(f"pydub.AudioSegment.converter configurado para: {ffmpeg_path}")
    
    if ffprobe_path:
        AudioSegment.ffprobe = ffprobe_path
        logger.info(f"pydub.AudioSegment.ffprobe configurado para: {ffprobe_path}")
    
    # Testar se o ffmpeg está funcionando
    if test_ffmpeg():
        logger.info("Teste do ffmpeg concluído com sucesso")
    else:
        logger.warning("Teste do ffmpeg falhou, pode haver problemas ao processar áudio/vídeo")
        
    # Verificar se os executáveis existem
    if hasattr(AudioSegment, 'converter') and os.path.exists(AudioSegment.converter):
        logger.info(f"Verificado: ffmpeg existe em {AudioSegment.converter}")
    else:
        logger.error(f"ERRO: ffmpeg não existe no caminho configurado: {getattr(AudioSegment, 'converter', 'não definido')}")
    
    if hasattr(AudioSegment, 'ffprobe') and os.path.exists(AudioSegment.ffprobe):
        logger.info(f"Verificado: ffprobe existe em {AudioSegment.ffprobe}")
    else:
        logger.error(f"ERRO: ffprobe não existe no caminho configurado: {getattr(AudioSegment, 'ffprobe', 'não definido')}")
        
except Exception as e:
    logger.error(f"Erro ao configurar ffmpeg/ffprobe: {e}")

# Corrigir os problemas de escape sequence na biblioteca pydub
try:
    # Importar o módulo utils da pydub para corrigir as expressões regulares
    from pydub import utils
    
    # Monkey patch para corrigir as expressões regulares com escape sequences inválidas
    if hasattr(utils, 're'):
        # Substituir diretamente as expressões regulares problemáticas no módulo utils
        utils_content = utils.__dict__
        for name, value in utils_content.items():
            if isinstance(value, str) and ('(flt)' in value or '(dbl)' in value):
                # Corrigir os padrões problemáticos
                fixed_value = value.replace('(', '\\(')
                fixed_value = fixed_value.replace(')', '\\)')
                utils_content[name] = fixed_value
                logger.info(f"Corrigida expressão regular em utils.{name}")
        
        # Patch específico para as funções que usam re.match
        original_match = utils.re.match
        
        def patched_re_match(pattern, string, *args, **kwargs):
            if isinstance(pattern, str) and ('(flt)' in pattern or '(dbl)' in pattern):
                # Corrigir os padrões problemáticos
                pattern = pattern.replace('(', '\\(')
                pattern = pattern.replace(')', '\\)')
            return original_match(pattern, string, *args, **kwargs)
        
        # Aplicar o patch
        utils.re.match = patched_re_match
        logger.info("Aplicado patch para corrigir expressões regulares na pydub")
        
        # Suprimir avisos específicos de SyntaxWarning para escape sequences
        warnings.filterwarnings("ignore", category=SyntaxWarning, message="invalid escape sequence")
        logger.info("Configurado filtro para suprimir avisos de escape sequences inválidas")
except Exception as e:
    logger.error(f"Erro ao tentar corrigir expressões regulares na pydub: {e}")
    # Continuar mesmo com o erro

# Configuração para dispositivos móveis
def is_mobile_device(user_agent):
    """Verifica se o user-agent é de um dispositivo móvel"""
    mobile_identifiers = [
        "android", "iphone", "ipad", "ipod", "windows phone", "blackberry", "mobile", "mobi"
    ]
    return any(identifier in user_agent.lower() for identifier in mobile_identifiers)