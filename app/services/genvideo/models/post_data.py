from dataclasses import dataclass
from datetime import datetime

@dataclass
class PostData:
    guid: str
    solicitacao: str
    titulo: str
    roteiro: str
    frases: list
    hashtags: list
    conteudo: str
    imagens: list
    narracao_marcada: str
    arquivo_narracao_raw: str
    arquivo_narracao_remix: str
    arquivo_video: str
    data_registro: datetime = datetime.now()