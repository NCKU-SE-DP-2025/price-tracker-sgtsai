from apscheduler.schedulers.background import BackgroundScheduler
from app.db.session import SessionLocal
from app.services.news_service import NewsService
from app.core.config import API_KEY

scheduler = BackgroundScheduler()

def preload_news():
    db = SessionLocal()
    service = NewsService(db, API_KEY)
    mock_news = [
        {"title": "物價上漲", "titleLink": "https://example.com/init1"},
        {"title": "通膨影響", "titleLink": "https://example.com/init2"},
    ]
    for item in mock_news:
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
