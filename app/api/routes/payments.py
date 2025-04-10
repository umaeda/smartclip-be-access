from typing import Any, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_verified_user, csrf_protect
from app.models.user import User
from app.schemas.payment import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentConfirm,
    PaymentConfirmResponse,
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionStatus,
    SubscriptionCancel,
    SubscriptionCancelResponse
)
from app.services.payment_service import (
    create_payment_intent,
    confirm_payment,
    create_checkout_session,
    create_subscription,
    get_subscription_status,
    cancel_subscription,
    PaymentException
)
from app.core.exceptions import map_domain_exception_to_http
from app.core.logger import get_logger

logger = get_logger("payments_router")

router = APIRouter()


@router.post("/create-intent", response_model=PaymentIntentResponse)
def create_payment_intent_endpoint(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    payment_data: PaymentIntentCreate
) -> Any:
    """Cria uma intenção de pagamento no Stripe"""
    try:
        # Determina o valor e moeda com base no planID
        amount = 0
        currency = "brl"
        
        # Implementa a lógica de case para os planos
        if payment_data.planId == "plan_starter":
            amount = 200
            currency = "brl"
        else:
            # Caso o planId não seja reconhecido
            raise PaymentException(detail=f"Plano não reconhecido: {payment_data.planId}")
        
        logger.info(
            "Criando intenção de pagamento",
            extra={
                "user_id": current_user.id,
                "user_email": current_user.email,
                "planID": payment_data.planId,
                "amount": amount,
                "currency": currency,
                "operation": "create_payment_intent"
            }
        )
        
        result = create_payment_intent(
            db, 
            current_user.id, 
            amount, 
            currency
        )
        
        return result
    
    except PaymentException as e:
        # Mapeia exceções de domínio para exceções HTTP
        raise map_domain_exception_to_http(e)
    
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro não tratado ao criar intenção de pagamento",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": current_user.id,
                "operation": "create_payment_intent"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar pagamento. ID do erro: {error_id}"
        )


@router.post("/confirm", response_model=PaymentConfirmResponse)
def confirm_payment_endpoint(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    payment_data: PaymentConfirm
) -> Any:
    """Confirma um pagamento no Stripe"""
    try:
        logger.info(
            "Confirmando pagamento",
            extra={
                "user_id": current_user.id,
                "user_email": current_user.email,
                "payment_intent_id": payment_data.payment_intent_id,
                "operation": "confirm_payment"
            }
        )
        
        result = confirm_payment(db, payment_data.payment_intent_id)
        
        return result
    
    except PaymentException as e:
        # Mapeia exceções de domínio para exceções HTTP
        raise map_domain_exception_to_http(e)
    
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro não tratado ao confirmar pagamento",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": current_user.id,
                "payment_intent_id": payment_data.payment_intent_id,
                "operation": "confirm_payment"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao confirmar pagamento. ID do erro: {error_id}"
        )


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session_endpoint(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    checkout_data: CheckoutSessionCreate
) -> Any:
    """Cria uma sessão de checkout no Stripe para finalizar o pagamento"""
    try:
        logger.info(
            "Criando sessão de checkout",
            extra={
                "user_id": current_user.id,
                "user_email": current_user.email,
                "payment_intent_id": checkout_data.payment_intent_id,
                "operation": "create_checkout_session"
            }
        )
        
        result = create_checkout_session(
            db, 
            checkout_data.payment_intent_id,
            checkout_data.success_url,
            checkout_data.cancel_url
        )
        
        return result
    
    except PaymentException as e:
        # Mapeia exceções de domínio para exceções HTTP
        raise map_domain_exception_to_http(e)
    
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro não tratado ao criar sessão de checkout",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": current_user.id,
                "payment_intent_id": checkout_data.payment_intent_id,
                "operation": "create_checkout_session"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar sessão de checkout. ID do erro: {error_id}"
        )


@router.get("/subscription-status", response_model=SubscriptionStatus)
def get_subscription_status_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """Verifica o status da assinatura do usuário"""
    try:
        logger.info(
            "Verificando status da assinatura",
            extra={
                "user_id": current_user.id,
                "user_email": current_user.email,
                "operation": "get_subscription_status"
            }
        )
        
        result = get_subscription_status(db, current_user.id)
        
        return result
    
    except Exception as e:
        # Tratamento genérico para erros
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao verificar status da assinatura",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": current_user.id,
                "operation": "get_subscription_status"
            }
        )
        # Retorna um status de erro, mas não lança exceção para não interromper o fluxo
        return {
            "has_subscription": False,
            "status": "error",
            "plan_type": "free",
            "error": f"Erro ao verificar status da assinatura. ID do erro: {error_id}"
        }


@router.post("/cancel-subscription", response_model=SubscriptionCancelResponse)
def cancel_subscription_endpoint(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    cancel_data: SubscriptionCancel
) -> Any:
    """Cancela a assinatura do usuário"""
    try:
        logger.info(
            "Cancelando assinatura",
            extra={
                "user_id": current_user.id,
                "user_email": current_user.email,
                "cancel_immediately": cancel_data.cancel_immediately,
                "operation": "cancel_subscription"
            }
        )
        
        result = cancel_subscription(db, current_user.id, cancel_data.cancel_immediately)
        
        return result
    
    except PaymentException as e:
        # Mapeia exceções de domínio para exceções HTTP
        raise map_domain_exception_to_http(e)
    
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro não tratado ao cancelar assinatura",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": current_user.id,
                "operation": "cancel_subscription"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cancelar assinatura. ID do erro: {error_id}"
        )