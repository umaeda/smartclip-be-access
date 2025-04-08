import os
import sys
from pydub import AudioSegment

# Configuração explícita dos caminhos do ffmpeg para o Heroku
if os.environ.get('FFMPEG_PATH'):
    AudioSegment.converter = os.environ.get('FFMPEG_PATH')
else:
    # Tenta encontrar ffmpeg no PATH do sistema
    import shutil
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        AudioSegment.converter = ffmpeg_path

if os.environ.get('FFPROBE_PATH'):
    AudioSegment.ffprobe = os.environ.get('FFPROBE_PATH')
else:
    # Tenta encontrar ffprobe no PATH do sistema
    import shutil
    ffprobe_path = shutil.which('ffprobe')
    if ffprobe_path:
        AudioSegment.ffprobe = ffprobe_path

# Configuração para dispositivos móveis
def is_mobile_device(user_agent):
    """Verifica se o user-agent é de um dispositivo móvel"""
    mobile_identifiers = [
        "android", "iphone", "ipad", "ipod", "windows phone", "blackberry", "mobile", "mobi"
    ]
    return any(identifier in user_agent.lower() for identifier in mobile_identifiers)