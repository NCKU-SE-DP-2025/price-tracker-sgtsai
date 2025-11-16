from typing import Optional
from fastapi import HTTPException, status
from jose import jwt, JWTError

from app.models.user import User
from app.core.config import SECRET_KEY, ALGORITHM
from app.core.security import verify_password

class UserService:
    def __init__(self, db):
        self.db = db

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Return User when credentials are valid, otherwise return None.
        """
        user = self.db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    def decode_token(self, token: str) -> User:
        """
        Decode JWT and return the User. Raises HTTPException on any error.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token verification failed")

        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
