from datetime import datetime, timedelta
from typing import Any, Optional, Union, Dict, Tuple
from collections import defaultdict
import logging

from jose import jwt
from passlib.context import CryptContext
from argon2 import PasswordHasher

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
argon2_hasher = PasswordHasher()

JWT_ALGORITHM = "HS256"


class BruteForceProtection:
    def __init__(self, max_attempts: int = 5, lockout_minutes: int = 15):
        """
        Initialize brute force protection with configurable settings
        
        Args:
            max_attempts: Maximum number of failed attempts before lockout
            lockout_minutes: Duration of lockout in minutes
        """
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        
        # Track failed attempts by username/email and IP address
        self.failed_attempts: Dict[str, list] = defaultdict(list)
        self.locked_accounts: Dict[str, datetime] = {}
    
    def _clean_old_attempts(self, identifier: str) -> None:
        """
        Remove attempts older than the lockout period
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=self.lockout_minutes)
        
        self.failed_attempts[identifier] = [
            attempt_time for attempt_time in self.failed_attempts[identifier]
            if attempt_time > cutoff
        ]
        
        # Remove expired lockouts
        expired_locks = []
        for account, lock_time in self.locked_accounts.items():
            if lock_time < cutoff:
                expired_locks.append(account)
                
        for account in expired_locks:
            del self.locked_accounts[account]
    
    def check_account_status(self, identifier: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if an account is locked and when it will be unlocked
        
        Args:
            identifier: Username, email, or other unique identifier
            
        Returns:
            Tuple[bool, Optional[datetime]]: (is_locked, unlock_time)
        """
        self._clean_old_attempts(identifier)
        
        # Check if account is locked
        if identifier in self.locked_accounts:
            unlock_time = self.locked_accounts[identifier] + timedelta(minutes=self.lockout_minutes)
            return True, unlock_time
        
        # Check if account should be locked based on recent attempts
        recent_attempts = len(self.failed_attempts[identifier])
        if recent_attempts >= self.max_attempts:
            # Lock the account
            self.locked_accounts[identifier] = datetime.now()
            unlock_time = self.locked_accounts[identifier] + timedelta(minutes=self.lockout_minutes)
            logger.warning(f"Account {identifier} locked due to too many failed attempts")
            return True, unlock_time
        
        return False, None
    
    def record_failed_attempt(self, identifier: str) -> Tuple[int, bool]:
        """
        Record a failed login attempt and check if account should be locked
        
        Args:
            identifier: Username, email, or other unique identifier
            
        Returns:
            Tuple[int, bool]: (attempts_remaining, is_locked)
        """
        self._clean_old_attempts(identifier)
        
        # Check if already locked
        is_locked, _ = self.check_account_status(identifier)
        if is_locked:
            return 0, True
        
        # Record the failed attempt
        self.failed_attempts[identifier].append(datetime.now())
        
        # Check if account should now be locked
        recent_attempts = len(self.failed_attempts[identifier])
        attempts_remaining = max(0, self.max_attempts - recent_attempts)
        
        if attempts_remaining == 0:
            # Lock the account
            self.locked_accounts[identifier] = datetime.now()
            logger.warning(f"Account {identifier} locked due to too many failed attempts")
            return 0, True
        
        return attempts_remaining, False
    
    def reset_attempts(self, identifier: str) -> None:
        """
        Reset failed attempts after successful login
        
        Args:
            identifier: Username, email, or other unique identifier
        """
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
        
        if identifier in self.locked_accounts:
            del self.locked_accounts[identifier]


# Global instance for application-wide use
brute_force_protection = BruteForceProtection()


def create_access_token(subject: str, expires_delta: timedelta = None, user_data: dict = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # Add user data to token if provided
    if user_data:
        to_encode.update(user_data)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica a senha contra um hash, detectando o algoritmo"""

    if hashed_password.startswith("$argon2"):
        # Verifica usando Argon2
        try:
            return argon2_hasher.verify(hashed_password, plain_password)
        except Exception:
            return False
    else:
        # Verifica usando Bcrypt
        return password_context.verify(plain_password, hashed_password)



def get_password_hash(password: str) -> str:
    """Generate a password hash using Argon2"""
    return argon2_hasher.hash(password)