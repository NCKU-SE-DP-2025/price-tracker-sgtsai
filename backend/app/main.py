from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import users, news, prices
from app.core.scheduler import start_scheduler, shutdown_scheduler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/v1/users")
app.include_router(news.router, prefix="/api/v1/news")
app.include_router(prices.router, prefix="/api/v1/prices")

@app.on_event("startup")
def startup_event():
    start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()
    
from app.db.base import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)
