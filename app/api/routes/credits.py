from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_verified_user, csrf_protect, has_permission
from app.models.user import User
from app.schemas.video_credit import VideoCredit, VideoCreditTransaction, VideoCreditWithTransactions
from app.services.credit_service import (
    check_user_credit_balance, 
    get_user_credit, 
    get_credit_transactions,
    add_credits,
    CreditTransactionException
)
from app.core.exceptions import map_domain_exception_to_http
from app.core.logger import get_logger

logger = get_logger("credits_router")

router = APIRouter()


@router.get("/balance", response_model=VideoCredit)
def get_credit_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """Obtém o saldo de créditos do usuário atual"""
    logger.info(
        "Consultando saldo de créditos",
        extra={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "operation": "get_credit_balance"
        }
    )
    
    credit = get_user_credit(db, current_user.id)
    return credit


@router.get("/transactions", response_model=List[VideoCreditTransaction])
def get_user_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """Obtém o histórico de transações de crédito do usuário atual"""
    logger.info(
        "Consultando histórico de transações de crédito",
        extra={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "skip": skip,
            "limit": limit,
            "operation": "get_credit_transactions"
        }
    )
    
    transactions = get_credit_transactions(db, current_user.id, skip, limit)
    return transactions


@router.post("/add", response_model=VideoCredit, dependencies=[Depends(csrf_protect())])
def add_user_credits(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("adicionar_creditos")),
    amount: int,
    description: str = "Compra de créditos"
) -> Any:
    """Adiciona créditos ao usuário (simulação de compra)"""
    try:
        logger.info(
            "Adicionando créditos ao usuário",
            extra={
                "user_id": current_user.id,
                "user_email": current_user.email,
                "amount": amount,
                "operation": "add_credits"
            }
        )
        
        credit, _ = add_credits(db, current_user.id, amount, description)
        return credit
    
    except CreditTransactionException as e:
        # Mapeia exceções de domínio para exceções HTTP
        raise map_domain_exception_to_http(e)
    
    except Exception as e:
        # Tratamento genérico para outros erros não esperados
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro não tratado ao adicionar créditos",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": current_user.id,
                "amount": amount,
                "operation": "add_credits"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "internal_server_error",
                "message": "Erro interno do servidor",
                "error_id": error_id
            }
        )