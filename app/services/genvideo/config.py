# Configurações globais
import os

IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
TEMAS = ["Tecnologia", "Educação", "Entretenimento", "Saúde"]

API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "stablediffusion": os.getenv("SD_API_KEY"),
    "youtube": os.getenv("YT_API_KEY")
}