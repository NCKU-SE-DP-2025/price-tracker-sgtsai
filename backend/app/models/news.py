from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.association import user_news_association_table

class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship("User", secondary=user_news_association_table, back_populates="upvoted_news")
