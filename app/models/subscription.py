from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class Subscription(Base):
    """
    Modelo para armazenar informações de assinaturas de usuários.
    Cada assinatura está vinculada a um usuário e contém informações do Stripe.
    """
    user_id = Column(Integer, ForeignKey("tb_user.id"), nullable=False, index=True)
    stripe_customer_id = Column(String, nullable=True)  # ID do cliente no Stripe
    stripe_subscription_id = Column(String, nullable=True)  # ID da assinatura no Stripe
    status = Column(String, nullable=False, default="inactive")  # active, inactive, canceled, etc.
    plan_type = Column(String, nullable=False, default="free")  # free, premium, etc.
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", backref="subscription")
    
    def __repr__(self):
        return f"<Subscription user_id={self.user_id} status={self.status} plan={self.plan_type}>"