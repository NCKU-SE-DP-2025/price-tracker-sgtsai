from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.schemas.news import NewsSummaryRequest
from app.schemas.prompt import PromptRequest
from app.db.session import SessionLocal
from app.services.news_service import NewsService
from app.services.user_service import UserService
from app.utils.openai_util import OpenAIUtil
from app.core.config import API_KEY

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/all")
def read_news(db: Session = Depends(get_db)):
    service = NewsService(db, API_KEY)
    return service.get_all_news()

@router.get("/user")
def read_user_news(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = UserService(db).decode_token(token)
    service = NewsService(db, API_KEY)
    return service.get_user_news(user)

@router.post("/{id}/upvote")
def upvote_article(id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = UserService(db).decode_token(token)
    message = NewsService(db, API_KEY).toggle_upvote(id, user.id)
    return {"message": message}

@router.post("/summary")
def summarize_news(payload: NewsSummaryRequest, db: Session = Depends(get_db)):
    service = NewsService(db, API_KEY)
    return service.summarize_article([payload.content])

@router.post("/search")
def search_news(request: PromptRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = UserService(db).decode_token(token)
    openai_util = OpenAIUtil(API_KEY)
    keywords = openai_util.extract_keywords(request.prompt)

    def fetch_news_mock(keyword: str):
        return [
            {"title": f"{keyword} 價格上漲", "titleLink": "https://example.com/news1"},
            {"title": f"{keyword} 市場趨勢", "titleLink": "https://example.com/news2"},
        ]

    news_items = fetch_news_mock(keywords)
    service = NewsService(db, API_KEY)
    results = []

    for item in news_items:
        try:
            article = service.scraper.fetch_article_content(item["titleLink"])
            summary = service.summarize_article(article["content"])
            article.update(summary)
            results.append(article)
        except Exception as e:
            print(f"Error processing article: {e}")

    return results
