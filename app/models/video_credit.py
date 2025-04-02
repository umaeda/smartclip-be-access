from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class VideoCredit(Base):
    """
    Modelo para armazenar o saldo de créditos de vídeo de cada usuário.
    Cada usuário tem direito a um número limitado de vídeos que pode gerar.
    """
    user_id = Column(Integer, ForeignKey("tb_user.id"), nullable=False, unique=True)
    balance = Column(Integer, default=10, nullable=False)  # Saldo inicial de 10 vídeos
    
    # Relacionamentos
    user = relationship("User", backref="video_credit")
    transactions = relationship("VideoCreditTransaction", back_populates="video_credit")
    
    def __repr__(self):
        return f"<VideoCredit user_id={self.user_id} balance={self.balance}>"