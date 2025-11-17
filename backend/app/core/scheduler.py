from apscheduler.schedulers.background import BackgroundScheduler
from app.db.session import SessionLocal
from app.services.news_service import NewsService
from app.core.config import API_KEY
from app.api.v1.news import get_new_info
from app.models.news import NewsArticle
scheduler = BackgroundScheduler()

def preload_news(is_initial=False):
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        service = NewsService(db, API_KEY)
        news_data = get_new_info("價格", is_initial=is_initial)
        for item in news_data:
            try:
                service.process_news_item(item)
            except Exception as e:
                print(f"Scheduler error: {e}")
    db.close()

def start_scheduler():
    scheduler.add_job(preload_news, "interval", minutes=100)
    scheduler.start()

def shutdown_scheduler():
    scheduler.shutdown()
