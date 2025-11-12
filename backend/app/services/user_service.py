from fastapi import HTTPException
from jose import jwt, JWTError
from app.models.user import User
from app.core.config import JWT_SECRET

class UserService:
    def __init__(self, db):
        self.db = db

    def decode_token(self, token: str) -> User:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token payload")
        except JWTError:
            raise HTTPException(status_code=401, detail="Token verification failed")

        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
