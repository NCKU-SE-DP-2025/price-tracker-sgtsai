from app.utils.scraper import ScraperUtil
from app.utils.openai_util import OpenAIUtil
from app.models.news import NewsArticle
from app.models.association import user_news_association_table
from sqlalchemy import select, insert, delete

class NewsService:
    def __init__(self, db, api_key):
        self.db = db
        self.openai = OpenAIUtil(api_key)
        self.scraper = ScraperUtil

    def add_article(self, article_data):
        article = NewsArticle(**article_data)
        self.db.add(article)
        self.db.commit()
        self.db.close()

    def summarize_article(self, content):
        return self.openai.generate_summary(" ".join(content))

    def process_news_item(self, news):
        relevance = self.openai.evaluate_relevance(news["title"])
        if relevance != "high":
            return
        article = ScraperUtil.fetch_article_content(news["titleLink"])
        summary = self.summarize_article(article["content"])
        article.update(summary)
        self.add_article(article)

    def toggle_upvote(self, news_id, user_id):
        existing = self.db.execute(
            select(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == news_id,
                user_news_association_table.c.user_id == user_id
            )
        ).scalar()
        if existing:
            self.db.execute(
                delete(user_news_association_table).where(
                    user_news_association_table.c.news_articles_id == news_id,
                    user_news_association_table.c.user_id == user_id
                )
            )
            self.db.commit()
            return "Upvote removed"
        else:
            self.db.execute(
                insert(user_news_association_table).values(
                    news_articles_id=news_id,
                    user_id=user_id
                )
            )
            self.db.commit()
            return "Article upvoted"

    def get_all_news(self):
        articles = self.db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
        return [
            {
                **article.__dict__,
                "upvotes": len(article.upvoted_by_users),
                "is_upvoted": False
            }
            for article in articles
        ]

    def get_user_news(self, user):
        articles = self.db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
        return [
            {
                **article.__dict__,
                "upvotes": len(article.upvoted_by_users),
                "is_upvoted": user in article.upvoted_by_users
            }
            for article in articles
        ]
