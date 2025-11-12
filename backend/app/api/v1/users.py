from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.schemas.user import UserAuthSchema
from app.db.session import SessionLocal
from app.core.security import hash_password, verify_password, create_access_token
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user: UserAuthSchema, db: Session = Depends(get_db)):
    hashed = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = UserService(db).decode_token(token)
    return {"username": user.username}
