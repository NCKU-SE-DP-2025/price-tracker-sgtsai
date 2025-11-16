from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///news.db")
SessionLocal = sessionmaker(bind=engine)
# Dependency for FastAPI
def session_opener():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()