from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# Esquema para transações de crédito
class VideoCreditTransactionBase(BaseModel):
    amount: int
    transaction_type: str
    description: Optional[str] = None

class VideoCreditTransaction(VideoCreditTransactionBase):
    id: int
    balance_after: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquema para créditos de vídeo
class VideoCreditBase(BaseModel):
    balance: int

class VideoCredit(VideoCreditBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VideoCreditWithTransactions(VideoCredit):
    transactions: List[VideoCreditTransaction] = []
    
    class Config:
        from_attributes = True