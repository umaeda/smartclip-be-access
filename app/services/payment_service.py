import os
import stripe
from typing import Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription
from app.core.exceptions import DomainException
from app.core.logger import get_logger
from app.services.credit_service import add_credits

logger = get_logger("payment_service")

# Configuração do Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentException(DomainException):
    """Lançada quando ocorre um erro no processamento de pagamentos"""
    def __init__(self, detail: str = "Erro ao processar pagamento", error_id: str = None):
        self.detail = detail
        self.error_id = error_id
        super().__init__(self.detail)


def create_payment_intent(db: Session, user_id: int, amount: int, currency: str = "brl") -> Dict[str, Any]:
    """
    Cria uma intenção de pagamento no Stripe.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        amount: Valor em centavos
        currency: Moeda (padrão: BRL)
        
    Returns:
        Dict: Dados da intenção de pagamento, incluindo client_secret
    """
    try:
        # Busca o usuário
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise PaymentException(detail="Usuário não encontrado")
        
        # Busca ou cria o registro de assinatura do usuário
        subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        if not subscription:
            subscription = Subscription(user_id=user_id)
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
        
        # Cria ou recupera o cliente no Stripe
        if not subscription.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user_id)}
            )
            subscription.stripe_customer_id = customer.id
            db.commit()
        
        # Cria a intenção de pagamento
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            customer=subscription.stripe_customer_id,
            metadata={"user_id": str(user_id)},  # Converte user_id para string para garantir compatibilidade
            automatic_payment_methods={"enabled": True}
        )
        
        logger.info(
            "Intenção de pagamento criada com sucesso",
            extra={
                "user_id": user_id,
                "payment_intent_id": intent.id,
                "amount": amount,
                "currency": currency,
                "operation": "create_payment_intent"
            }
        )
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": amount,
            "currency": currency
        }
    
    except stripe.error.StripeError as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro do Stripe ao criar intenção de pagamento",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "amount": amount,
                "operation": "create_payment_intent"
            }
        )
        raise PaymentException(
            detail=f"Erro ao processar pagamento: {str(e)}",
            error_id=error_id
        )
    
    except Exception as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao criar intenção de pagamento",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "amount": amount,
                "operation": "create_payment_intent"
            }
        )
        raise PaymentException(
            detail="Falha ao processar pagamento",
            error_id=error_id
        )


def confirm_payment(db: Session, payment_intent_id: str) -> Dict[str, Any]:
    """
    Confirma um pagamento e atualiza o status da assinatura do usuário.
    
    Args:
        db: Sessão do banco de dados
        payment_intent_id: ID da intenção de pagamento
        
    Returns:
        Dict: Dados do pagamento confirmado
    """
    try:
        # Recupera a intenção de pagamento do Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status != "succeeded":
            raise PaymentException(detail=f"Pagamento não confirmado. Status: {intent.status}")
        
        # Recupera o ID do usuário dos metadados
        user_id = intent.metadata.get("user_id")
        if not user_id:
            raise PaymentException(detail="ID do usuário não encontrado nos metadados do pagamento")
        
        # Converte para inteiro
        try:
            user_id = int(user_id)
        except ValueError:
            raise PaymentException(detail="ID do usuário inválido")
        
        # Adiciona créditos ao usuário com base no valor pago
        # Aqui você pode definir uma regra de conversão de valor para créditos
        amount_paid = intent.amount
        credits_to_add = amount_paid // 1000  # Exemplo: 1 crédito para cada R$ 10,00
        
        if credits_to_add > 0:
            credit, transaction = add_credits(
                db, 
                user_id, 
                credits_to_add, 
                description=f"Compra de créditos via Stripe - {payment_intent_id}"
            )
        
        logger.info(
            "Pagamento confirmado com sucesso",
            extra={
                "user_id": user_id,
                "payment_intent_id": payment_intent_id,
                "amount_paid": amount_paid,
                "credits_added": credits_to_add,
                "operation": "confirm_payment"
            }
        )
        
        return {
            "status": "success",
            "payment_intent_id": payment_intent_id,
            "amount_paid": amount_paid,
            "credits_added": credits_to_add,
            "new_balance": credit.balance if credits_to_add > 0 else None
        }
    
    except stripe.error.StripeError as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro do Stripe ao confirmar pagamento",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "payment_intent_id": payment_intent_id,
                "operation": "confirm_payment"
            }
        )
        raise PaymentException(
            detail=f"Erro ao confirmar pagamento: {str(e)}",
            error_id=error_id
        )
    
    except Exception as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao confirmar pagamento",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "payment_intent_id": payment_intent_id,
                "operation": "confirm_payment"
            }
        )
        raise PaymentException(
            detail="Falha ao confirmar pagamento",
            error_id=error_id
        )


def create_subscription(db: Session, user_id: int, price_id: str) -> Dict[str, Any]:
    """
    Cria uma assinatura para o usuário.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        price_id: ID do preço/plano no Stripe
        
    Returns:
        Dict: Dados da assinatura criada
    """
    try:
        # Busca o usuário
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise PaymentException(detail="Usuário não encontrado")
        
        # Busca ou cria o registro de assinatura do usuário
        subscription_record = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        if not subscription_record:
            subscription_record = Subscription(user_id=user_id)
            db.add(subscription_record)
            db.commit()
            db.refresh(subscription_record)
        
        # Cria ou recupera o cliente no Stripe
        if not subscription_record.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user_id)}
            )
            subscription_record.stripe_customer_id = customer.id
            db.commit()
        
        # Cria a assinatura no Stripe
        subscription = stripe.Subscription.create(
            customer=subscription_record.stripe_customer_id,
            items=[
                {"price": price_id},
            ],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
            metadata={"user_id": str(user_id)}
        )
        
        # Atualiza o registro de assinatura no banco de dados
        subscription_record.stripe_subscription_id = subscription.id
        subscription_record.status = subscription.status
        subscription_record.plan_type = "premium"  # Ou o tipo de plano correspondente
        subscription_record.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
        subscription_record.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        db.commit()
        
        # Atualiza o tipo de perfil do usuário
        user.profile_type = "Gold"  # Ou o tipo correspondente ao plano
        db.commit()
        
        logger.info(
            "Assinatura criada com sucesso",
            extra={
                "user_id": user_id,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "plan_type": "premium",
                "operation": "create_subscription"
            }
        )
        
        # Retorna os dados necessários para o frontend completar o pagamento
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret,
            "status": subscription.status
        }
    
    except stripe.error.StripeError as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro do Stripe ao criar assinatura",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "price_id": price_id,
                "operation": "create_subscription"
            }
        )
        raise PaymentException(
            detail=f"Erro ao criar assinatura: {str(e)}",
            error_id=error_id
        )
    
    except Exception as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao criar assinatura",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "price_id": price_id,
                "operation": "create_subscription"
            }
        )
        raise PaymentException(
            detail="Falha ao criar assinatura",
            error_id=error_id
        )


def get_subscription_status(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Verifica o status da assinatura do usuário.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        
    Returns:
        Dict: Dados da assinatura do usuário
    """
    try:
        # Busca o registro de assinatura do usuário
        subscription_record = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        
        if not subscription_record or not subscription_record.stripe_subscription_id:
            return {
                "has_subscription": False,
                "status": "inactive",
                "plan_type": "free"
            }
        
        # Se tiver uma assinatura, verifica o status atual no Stripe
        try:
            subscription = stripe.Subscription.retrieve(subscription_record.stripe_subscription_id)
            
            # Atualiza o registro no banco de dados se necessário
            if subscription_record.status != subscription.status:
                subscription_record.status = subscription.status
                subscription_record.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
                subscription_record.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                subscription_record.cancel_at_period_end = subscription.cancel_at_period_end
                db.commit()
            
            return {
                "has_subscription": True,
                "status": subscription.status,
                "plan_type": subscription_record.plan_type,
                "current_period_end": subscription_record.current_period_end.isoformat() if subscription_record.current_period_end else None,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError:
            # Se não conseguir recuperar do Stripe, usa os dados do banco
            return {
                "has_subscription": True,
                "status": subscription_record.status,
                "plan_type": subscription_record.plan_type,
                "current_period_end": subscription_record.current_period_end.isoformat() if subscription_record.current_period_end else None,
                "cancel_at_period_end": subscription_record.cancel_at_period_end
            }
    
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao verificar status da assinatura",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "operation": "get_subscription_status"
            }
        )
        # Retorna um status padrão em caso de erro
        return {
            "has_subscription": False,
            "status": "error",
            "plan_type": "free",
            "error": "Não foi possível verificar o status da assinatura"
        }


def create_checkout_session(db: Session, payment_intent_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
    """
    Cria uma sessão de checkout no Stripe para finalizar um pagamento.
    Em vez de reutilizar um PaymentIntent existente, cria uma nova sessão de checkout
    com os mesmos dados do PaymentIntent original.
    
    Args:
        db: Sessão do banco de dados
        payment_intent_id: ID da intenção de pagamento (usado apenas para referência)
        success_url: URL para redirecionamento em caso de sucesso
        cancel_url: URL para redirecionamento em caso de cancelamento
        
    Returns:
        Dict: Dados da sessão de checkout, incluindo a URL para redirecionamento
    """
    try:
        # Recupera a intenção de pagamento do Stripe apenas para obter os dados necessários
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == "succeeded":
            raise PaymentException(detail="Este pagamento já foi processado")
        
        # Recupera o ID do usuário dos metadados
        user_id = intent.metadata.get("user_id")
        if not user_id:
            raise PaymentException(detail="ID do usuário não encontrado nos metadados do pagamento")
        
        # Cria uma nova sessão de checkout sem vincular ao PaymentIntent existente
        checkout_session = stripe.checkout.Session.create(
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            customer=intent.customer,
            client_reference_id=user_id,  # Adiciona referência ao usuário
            metadata={
                "user_id": user_id,
                "original_payment_intent_id": payment_intent_id  # Mantém referência ao PaymentIntent original
            },
            line_items=[
                {
                    "price_data": {
                        "currency": intent.currency,
                        "product_data": {
                            "name": "Créditos SmartClip",
                            "description": "Compra de créditos para geração de vídeos",
                        },
                        "unit_amount": intent.amount,
                    },
                    "quantity": 1,
                },
            ])
        
        logger.info(
            "Sessão de checkout criada com sucesso",
            extra={
                "user_id": user_id,
                "payment_intent_id": payment_intent_id,
                "checkout_session_id": checkout_session.id,
                "operation": "create_checkout_session"
            }
        )
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "status": checkout_session.status
        }
    
    except stripe.error.StripeError as e:
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro do Stripe ao criar sessão de checkout",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "payment_intent_id": payment_intent_id,
                "operation": "create_checkout_session"
            }
        )
        raise PaymentException(
            detail=f"Erro ao criar sessão de checkout: {str(e)}",
            error_id=error_id
        )
    
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao criar sessão de checkout",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "payment_intent_id": payment_intent_id,
                "operation": "create_checkout_session"
            }
        )
        raise PaymentException(
            detail="Falha ao criar sessão de checkout",
            error_id=error_id
        )


def cancel_subscription(db: Session, user_id: int, cancel_immediately: bool = False) -> Dict[str, Any]:
    """
    Cancela a assinatura do usuário.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        cancel_immediately: Se True, cancela imediatamente; se False, cancela no final do período
        
    Returns:
        Dict: Resultado da operação de cancelamento
    """
    try:
        # Busca o registro de assinatura do usuário
        subscription_record = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        
        if not subscription_record or not subscription_record.stripe_subscription_id:
            raise PaymentException(detail="Usuário não possui assinatura ativa")
        
        # Cancela a assinatura no Stripe
        if cancel_immediately:
            # Cancelamento imediato
            canceled_subscription = stripe.Subscription.delete(
                subscription_record.stripe_subscription_id
            )
        else:
            # Cancelamento no final do período atual
            canceled_subscription = stripe.Subscription.modify(
                subscription_record.stripe_subscription_id,
                cancel_at_period_end=True
            )
        
        # Atualiza o registro no banco de dados
        subscription_record.status = canceled_subscription.status
        subscription_record.cancel_at_period_end = canceled_subscription.cancel_at_period_end
        db.commit()
        
        # Se cancelado imediatamente, atualiza o perfil do usuário
        if cancel_immediately or canceled_subscription.status == "canceled":
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.profile_type = "Free"
                db.commit()
        
        logger.info(
            "Assinatura cancelada com sucesso",
            extra={
                "user_id": user_id,
                "subscription_id": subscription_record.stripe_subscription_id,
                "cancel_immediately": cancel_immediately,
                "new_status": canceled_subscription.status,
                "operation": "cancel_subscription"
            }
        )
        
        return {
            "status": "success",
            "subscription_status": canceled_subscription.status,
            "cancel_at_period_end": canceled_subscription.cancel_at_period_end,
            "message": "Assinatura cancelada com sucesso" if cancel_immediately else "Assinatura será cancelada no final do período atual"
        }
    
    except stripe.error.StripeError as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro do Stripe ao cancelar assinatura",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "operation": "cancel_subscription"
            }
        )
        raise PaymentException(
            detail=f"Erro ao cancelar assinatura: {str(e)}",
            error_id=error_id
        )
    
    except Exception as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao cancelar assinatura",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "operation": "cancel_subscription"
            }
        )
        raise PaymentException(
            detail="Falha ao cancelar assinatura",
            error_id=error_id
        )