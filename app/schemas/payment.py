from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class PaymentIntentCreate(BaseModel):
    """Modelo para criação de uma intenção de pagamento"""
    planId: str

class PaymentIntentResponse(BaseModel):
    """Resposta da criação de uma intenção de pagamento"""
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str

class PaymentConfirm(BaseModel):
    """Modelo para confirmação de pagamento"""
    payment_intent_id: str

class PaymentConfirmResponse(BaseModel):
    """Resposta da confirmação de pagamento"""
    status: str
    payment_intent_id: str
    amount_paid: int
    credits_added: float
    new_balance: Optional[int] = None

class CheckoutSessionCreate(BaseModel):
    """Modelo para criação de uma sessão de checkout"""
    payment_intent_id: str
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    """Resposta da criação de uma sessão de checkout"""
    checkout_url: str
    session_id: str
    status: str

class SubscriptionCreate(BaseModel):
    """Modelo para criação de uma assinatura"""
    price_id: str

class SubscriptionResponse(BaseModel):
    """Resposta da criação de uma assinatura"""
    subscription_id: str
    client_secret: str
    status: str

class SubscriptionStatus(BaseModel):
    """Status da assinatura do usuário"""
    has_subscription: bool
    status: str
    plan_type: str
    current_period_end: Optional[str] = None
    cancel_at_period_end: Optional[bool] = None
    error: Optional[str] = None

class SubscriptionCancel(BaseModel):
    """Modelo para cancelamento de assinatura"""
    cancel_immediately: bool = False

class SubscriptionCancelResponse(BaseModel):
    """Resposta do cancelamento de assinatura"""
    status: str
    subscription_status: str
    cancel_at_period_end: bool
    message: str