# -------------------- Imports --------------------
import os
import json
import itertools
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote

import requests
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from fastapi import (
    APIRouter, FastAPI, HTTPException, Query, Depends, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy import (
    Column, ForeignKey, Integer, String, Table, Text,
    create_engine, delete, insert, select
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from openai import OpenAI

# -------------------- Database Setup --------------------

Base = declarative_base()

user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)

# from pydantic import BaseModel


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )

# -------------------- Engine and Session --------------------

engine = create_engine("sqlite:///news_database.db", echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------- Sentry Setup --------------------

sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

# -------------------- FastAPI App Setup --------------------

app = FastAPI()
bgs = BackgroundScheduler()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- OpenAI Utilities (Commented) --------------------

# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

#
# def extract_search_keywords(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

def add_new(news_data: dict):
    """
    Add a news article to the database.

    :param news_data: Dictionary containing news fields
    """
    session = Session()
    article = NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),  # 將內容list轉換為字串
        summary=news_data["summary"],
        reason=news_data["reason"],
    )
    session.add(article)
    session.commit()
    session.close()


def get_new_info(search_term: str, is_initial: bool = False) -> list:
    """Fetch news data from UDN API based on search term.

    :param search_term: Keyword to search for
    :param is_initial: Whether to fetch multiple pages
    :return: List of news data dictionaries
    """
    all_news_data = []
    # iterate pages to get more news data, not actually get all news data
    def fetch_page(page: int) -> list:
        params = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=params)

        return response.json().get("lists", [])
    
    if is_initial:
        for page in range(1, 10):
            all_news_data.append(get_new_info(page))
    else:
        all_news_data.append(get_new_info(1))
    return all_news_data

def summarize_article(content: list, api_key: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": " ".join(content)},
    ]
    response = OpenAI(api_key=api_key).chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return json.loads(response.choices[0].message.content)

def fetch_article_content(url: str) -> dict:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("h1", class_="article-content__title").text.strip()
    time = soup.find("time", class_="article-content__time").text.strip()
    section = soup.find("section", class_="article-content__editor")

    paragraphs = [
        p.text.strip()
        for p in section.find_all("p")
        if p.text.strip() and "▪" not in p.text
    ]

    return {
        "url": url,
        "title": title,
        "time": time,
        "content": paragraphs,
    }

def process_news_item(news: dict, api_key: str):
    title = news["title"]
    news_messages = [
        {
            "role": "system",
            "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
        },
        {"role": "user", "content": f"{title}"},
    ]
    ai = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=news_messages,
    )
    relevance = ai.choices[0].message.content
    if relevance != "high":
        return
    article = fetch_article_content(news["titleLink"])
    summary = summarize_article(article["content"], api_key)
    
    article["summary"] = summary["影響"]
    article["reason"] = summary["原因"]
    add_new(article)

def get_new(is_initial=False):
    news_data = get_new_info("價格", is_initial=is_initial)
    api_key = "xxx"
    for news in news_data:
        process_news_item(news, api_key)

@app.on_event("startup")
def start_scheduler():
    """Initialize background scheduler and preload news if database is empty."""
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        get_new()
    db.close()
    bgs.add_job(get_new, "interval", minutes=100)
    bgs.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    bgs.shutdown()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def session_opener():
    """Yield a SQLAlchemy session for dependency injection."""
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticate a user by verifying their password.

    Returns the user object if authentication succeeds, otherwise None.
    """
    user = db.query(User).filter(User.username == username).first()
    if not verify_password(password, user.hashed_password):
        return False
    return user

def authenticate_user_token(token: str = Depends(oauth2_scheme), db: Session = Depends(session_opener)) -> User:
    """Decode JWT token and return authenticated user."""
    try:
        payload = jwt.decode(token, '1892dhianiandowqd0n', algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)) -> str:
    """Generate JWT access token with expiration."""
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, '1892dhianiandowqd0n', algorithm="HS256")
    return encoded_jwt


@app.post("/api/v1/users/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(session_opener)
):
    """Authenticate user and return JWT token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

class UserAuthSchema(BaseModel):
    username: str
    password: str

@app.post("/api/v1/users/register")
def create_user(user: UserAuthSchema, db: Session = Depends(session_opener)):
    """create user"""
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/v1/users/me")
def read_users_me(user=Depends(authenticate_user_token)):
    return {"username": user.username}


_id_counter = itertools.count(start=1000000)


def get_article_upvote_details(article_id: int, uid: int, db: Session) -> tuple[int, bool]:
    """Return total upvotes and whether the user has voted on the article."""
    cnt = (
        db.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    voted = False
    if uid:
        voted = (
                db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=uid)
                .first()
                is not None
        )
    return cnt, voted


@app.get("/api/v1/news/news")
def read_news(db: Session = Depends(session_opener)):
    """
    Retrieve all news articles, ordered by most recent,
    and include upvote count and user vote status.
    """
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    return [
        {
            **article.__dict__,
            "upvotes": upvotes,
            "is_upvoted": is_upvoted
        }
        for article in articles
        for upvotes, is_upvoted in [get_article_upvote_details(article.id, None, db)]
    ]

@app.get("/api/v1/news/user_news")
def read_user_news(
    db: Session = Depends(session_opener),
    u: User = Depends(authenticate_user_token)
):
    """
    Retrieve all news articles with upvote count and user's vote status.
    """
    articles = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()

    return [
        {
            **article.__dict__,
            "upvotes": upvotes,
            "is_upvoted": is_upvoted
        }
        for article in articles
        for upvotes, is_upvoted in [get_article_upvote_details(article.id, u.id, db)]
    ]

class PromptRequest(BaseModel):
    prompt: str

def extract_keywords(prompt: str, api_key: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，"
                "請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。"
                "(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)"
            ),
        },
        {"role": "user", "content": prompt},
    ]
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    return response.choices[0].message.content.strip()

def fetch_article_details(url: str, id_generator) -> dict | None:
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("h1", class_="article-content__title").text
        time = soup.find("time", class_="article-content__time").text
        content_section = soup.find("section", class_="article-content__editor")

        paragraphs = [
            p.text.strip()
            for p in content_section.find_all("p")
            if p.text.strip() and "▪" not in p.text
        ]

        return {
            "id": next(id_generator),
            "url": url,
            "title": title,
            "time": time,
            "content": " ".join(paragraphs),
        }
    except Exception as e:
        print(f"Error fetching article from {url}: {e}")
        return None
    
@app.post("/api/v1/news/search_news")
async def search_news(request: PromptRequest):
    prompt = request.prompt
    api_key = "xxx"

    keywords = extract_keywords(prompt, api_key)
    # should change into simple factory pattern
    news_items = get_new_info(keywords, is_initial=False)

    news_list = []
    for news in news_items:
        article = fetch_article_details(news["titleLink"], _id_counter)
        if article:
            news_list.append(article)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

class NewsSumaryRequestSchema(BaseModel):
    content: str

def generate_news_summary(content: str, api_key: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 "
                "(影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})"
            ),
        },
        {"role": "user", "content": content},
    ]
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    result_text = response.choices[0].message.content.strip()

    try:
        result = json.loads(result_text)
        return {
            "summary": result.get("影響", ""),
            "reason": result.get("原因", "")
        }
    except json.JSONDecodeError:
        print(f"Failed to parse summary response: {result_text}")
        return {
            "summary": "",
            "reason": ""
        }


@app.post("/api/v1/news/news_summary")
async def news_summary(payload: NewsSumaryRequestSchema, u=Depends(authenticate_user_token)):
    api_key = "xxx"
    return generate_news_summary(payload.content, api_key)
#to here
@app.post("/api/v1/news/{id}/upvote")
def upvote_article(
        id,
        db=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    message = toggle_upvote(id, user.id, db)
    return {"message": message}


def toggle_upvote(news_id: int, user_id: int, db: Session) -> str:
    existing_upvote = db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
        db.execute(delete_stmt)
        db.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=news_id, user_id=user_id
        )
        db.execute(insert_stmt)
        db.commit()
        return "Article upvoted"


def news_exists(news_id: int, db: Session) -> bool:
    return db.query(NewsArticle).filter_by(id=news_id).first() is not None


@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
    category: str = Query(None),
    commodity: str = Query(None),
):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json()
