from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Float, JSON, ARRAY, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.db.base_class import Base

class Video(Base):
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    url = Column(String, nullable=True)
    is_validated = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("tb_user.id"), nullable=False)
    duration = Column(Integer, nullable=True)  # Duração do vídeo em segundos
    generation_time = Column(Float, nullable=True)  # Tempo de geração em segundos
    
    # Campos adicionais do vídeo
    solicitacao = Column(String, nullable=True)  # Solicitação original do usuário
    roteiro = Column(String, nullable=True)  # Roteiro do vídeo
    frases = Column(JSON, nullable=True)  # Frases para geração de imagens
    hashtags = Column(String, nullable=True)  # Hashtags do vídeo
    conteudo = Column(String, nullable=True)  # Conteúdo descritivo do vídeo
    imagens = Column(JSON, nullable=True)  # Lista de caminhos das imagens
    narracao_marcada = Column(String, nullable=True)  # Narração com marcações SSML
    arquivo_narracao_raw = Column(String, nullable=True)  # Caminho do arquivo de narração original
    arquivo_narracao_remix = Column(String, nullable=True)  # Caminho do arquivo de narração com remix
    arquivo_video = Column(String, nullable=True)  # Caminho do arquivo de vídeo final
    data_registro = Column(DateTime, default=datetime.now)  # Data de registro
    
    # Relationships
    user = relationship("User", back_populates="videos")
    
    def __repr__(self):
        return f"<Video {self.title}>"