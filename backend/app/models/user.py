from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.association import user_news_association_table

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    upvoted_news = relationship("NewsArticle", secondary=user_news_association_table, back_populates="upvoted_by_users")
