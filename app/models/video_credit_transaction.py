from sqlalchemy import Column, Integer, ForeignKey, String, Enum
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class VideoCreditTransaction(Base):
    """
    Modelo para registrar todas as transações de créditos de vídeo.
    Cada transação representa uma adição ou consumo de créditos.
    """
    video_credit_id = Column(Integer, ForeignKey("tb_video_credit.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Positivo para adição, negativo para consumo
    balance_after = Column(Integer, nullable=False)  # Saldo após a transação
    transaction_type = Column(Enum('purchase', 'consumption', 'refund', name='transaction_types'), nullable=False)
    description = Column(String, nullable=True)  # Descrição opcional da transação
    
    # Relacionamentos
    video_credit = relationship("VideoCredit", back_populates="transactions")
    
    def __repr__(self):
        return f"<VideoCreditTransaction id={self.id} type={self.transaction_type} amount={self.amount}>"