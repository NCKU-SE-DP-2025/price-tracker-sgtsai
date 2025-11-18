from shlex import quote
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
from app.api.v1.users import authenticate_user_token
import requests
from openai import OpenAI
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/news")
def read_news(db: Session = Depends(get_db)):
    service = NewsService(db, API_KEY)
    return service.get_all_news()

@router.get("/user_news")
def read_user_news(db: Session = Depends(get_db), user = Depends(authenticate_user_token)):
    service = NewsService(db, API_KEY)
    return service.get_user_news(user)

@router.post("/{id}/upvote")
def upvote_article(id: int, db: Session = Depends(get_db), user = Depends(authenticate_user_token)):
    message = NewsService(db, API_KEY).toggle_upvote(id, user.id)
    return {"message": message}

@router.post("/news_summary")
def summarize_news(payload: NewsSummaryRequest, db: Session = Depends(get_db)):
    service = NewsService(db, API_KEY)
    return service.summarize_article([payload.content])

def get_new_info(search_term, is_initial=False):
    """
    get new

    :param search_term:
    :param is_initial:
    :return:
    """
    all_news_data = []
    # iterate pages to get more news data, not actually get all news data
    if is_initial:
        a = []
        for p in range(1, 10):
            p2 = {
                "page": p,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=p2)
            a.append(response.json()["lists"])

        for l in a:
            all_news_data.append(l)
    else:
        p = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=p)

        all_news_data = response.json()["lists"]
    return all_news_data

@router.post("/search_news")
def search_news(request: PromptRequest, db: Session = Depends(get_db)):
    openai_util = OpenAIUtil(API_KEY)
    keywords = openai_util.extract_keywords(request.prompt)

    news_items = get_new_info(keywords, is_initial=False)
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