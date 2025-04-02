from typing import Optional, Dict, Any, Tuple
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User
from app.models.video_credit import VideoCredit
from app.models.video_credit_transaction import VideoCreditTransaction
from app.core.exceptions import DomainException
from app.core.logger import get_logger

logger = get_logger("credit_service")


class InsufficientCreditsException(DomainException):
    """Lançada quando um usuário não tem créditos suficientes para gerar um vídeo"""
    def __init__(self, detail: str = "Usuário não possui créditos suficientes para gerar vídeo"):
        self.detail = detail
        super().__init__(self.detail)


class CreditTransactionException(DomainException):
    """Lançada quando ocorre um erro na transação de créditos"""
    def __init__(self, detail: str = "Erro ao processar transação de créditos", error_id: str = None):
        self.detail = detail
        self.error_id = error_id
        super().__init__(self.detail)


def get_user_credit(db: Session, user_id: int) -> VideoCredit:
    """
    Obtém o registro de crédito do usuário. Se não existir, cria um novo com saldo inicial.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        
    Returns:
        VideoCredit: O objeto de crédito do usuário
    """
    credit = db.query(VideoCredit).filter(VideoCredit.user_id == user_id).first()
    
    if not credit:
        # Cria um novo registro de crédito com saldo inicial de 10
        credit = VideoCredit(user_id=user_id, balance=10)
        db.add(credit)
        db.commit()
        db.refresh(credit)
        
        logger.info(
            "Registro de crédito criado para usuário",
            extra={
                "user_id": user_id,
                "initial_balance": credit.balance,
                "operation": "create_credit"
            }
        )
    
    return credit


def check_user_credit_balance(db: Session, user_id: int) -> int:
    """
    Verifica o saldo de créditos do usuário.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        
    Returns:
        int: Saldo atual de créditos
    """
    credit = get_user_credit(db, user_id)
    return credit.balance


def consume_credit(
    db: Session, 
    user_id: int, 
    amount: int = 1, 
    description: str = "Geração de vídeo"
) -> Tuple[VideoCredit, VideoCreditTransaction]:
    """
    Consome créditos do usuário para gerar um vídeo.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        amount: Quantidade de créditos a consumir (padrão: 1)
        description: Descrição da transação
        
    Returns:
        Tuple[VideoCredit, VideoCreditTransaction]: O objeto de crédito atualizado e a transação criada
        
    Raises:
        InsufficientCreditsException: Se o usuário não tiver créditos suficientes
        CreditTransactionException: Se ocorrer um erro na transação
    """
    try:
        credit = get_user_credit(db, user_id)
        
        # Verifica se o usuário tem créditos suficientes
        if credit.balance < amount:
            logger.warning(
                "Usuário sem créditos suficientes",
                extra={
                    "user_id": user_id,
                    "current_balance": credit.balance,
                    "requested_amount": amount,
                    "operation": "consume_credit"
                }
            )
            raise InsufficientCreditsException()
        
        # Atualiza o saldo
        credit.balance -= amount
        
        # Registra a transação
        transaction = VideoCreditTransaction(
            video_credit_id=credit.id,
            amount=-amount,  # Valor negativo para consumo
            balance_after=credit.balance,
            transaction_type="consumption",
            description=description
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(credit)
        db.refresh(transaction)
        
        logger.info(
            "Crédito consumido com sucesso",
            extra={
                "user_id": user_id,
                "transaction_id": transaction.id,
                "amount": amount,
                "new_balance": credit.balance,
                "operation": "consume_credit"
            }
        )
        
        return credit, transaction
    
    except InsufficientCreditsException:
        db.rollback()
        raise
    
    except Exception as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao consumir crédito",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "amount": amount,
                "operation": "consume_credit"
            }
        )
        raise CreditTransactionException(
            detail="Falha ao processar consumo de crédito",
            error_id=error_id
        )


def add_credits(
    db: Session, 
    user_id: int, 
    amount: int, 
    description: str = "Compra de créditos"
) -> Tuple[VideoCredit, VideoCreditTransaction]:
    """
    Adiciona créditos ao usuário após uma compra.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        amount: Quantidade de créditos a adicionar
        description: Descrição da transação
        
    Returns:
        Tuple[VideoCredit, VideoCreditTransaction]: O objeto de crédito atualizado e a transação criada
        
    Raises:
        CreditTransactionException: Se ocorrer um erro na transação
    """
    try:
        credit = get_user_credit(db, user_id)
        
        # Atualiza o saldo
        credit.balance += amount
        
        # Registra a transação
        transaction = VideoCreditTransaction(
            video_credit_id=credit.id,
            amount=amount,  # Valor positivo para adição
            balance_after=credit.balance,
            transaction_type="purchase",
            description=description
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(credit)
        db.refresh(transaction)
        
        logger.info(
            "Créditos adicionados com sucesso",
            extra={
                "user_id": user_id,
                "transaction_id": transaction.id,
                "amount": amount,
                "new_balance": credit.balance,
                "operation": "add_credits"
            }
        )
        
        return credit, transaction
    
    except Exception as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao adicionar créditos",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "amount": amount,
                "operation": "add_credits"
            }
        )
        raise CreditTransactionException(
            detail="Falha ao processar adição de créditos",
            error_id=error_id
        )


def refund_credit(
    db: Session, 
    user_id: int, 
    amount: int = 1, 
    description: str = "Estorno por falha na geração de vídeo"
) -> Tuple[VideoCredit, VideoCreditTransaction]:
    """
    Estorna créditos para o usuário após uma falha na geração de vídeo.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        amount: Quantidade de créditos a estornar (padrão: 1)
        description: Descrição da transação de estorno
        
    Returns:
        Tuple[VideoCredit, VideoCreditTransaction]: O objeto de crédito atualizado e a transação criada
        
    Raises:
        CreditTransactionException: Se ocorrer um erro na transação
    """
    try:
        credit = get_user_credit(db, user_id)
        
        # Atualiza o saldo
        credit.balance += amount
        
        # Registra a transação
        transaction = VideoCreditTransaction(
            video_credit_id=credit.id,
            amount=amount,  # Valor positivo para estorno
            balance_after=credit.balance,
            transaction_type="refund",
            description=description
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(credit)
        db.refresh(transaction)
        
        logger.info(
            "Crédito estornado com sucesso",
            extra={
                "user_id": user_id,
                "transaction_id": transaction.id,
                "amount": amount,
                "new_balance": credit.balance,
                "operation": "refund_credit"
            }
        )
        
        return credit, transaction
    
    except Exception as e:
        db.rollback()
        error_id = str(uuid.uuid4())
        logger.error(
            "Erro ao estornar crédito",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_id": error_id,
                "user_id": user_id,
                "amount": amount,
                "operation": "refund_credit"
            }
        )
        raise CreditTransactionException(
            detail="Falha ao processar estorno de crédito",
            error_id=error_id
        )


def get_credit_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    Obtém o histórico de transações de crédito do usuário.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        skip: Número de registros para pular (paginação)
        limit: Número máximo de registros a retornar
        
    Returns:
        List[VideoCreditTransaction]: Lista de transações do usuário
    """
    credit = get_user_credit(db, user_id)
    
    transactions = db.query(VideoCreditTransaction)\
        .filter(VideoCreditTransaction.video_credit_id == credit.id)\
        .order_by(VideoCreditTransaction.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return transactions