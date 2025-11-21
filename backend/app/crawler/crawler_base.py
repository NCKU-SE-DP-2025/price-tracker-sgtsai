import abc
import requests
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl, BaseModel, Field
from tldextract import tldextract
from sqlalchemy.orm import Session
from .exceptions import DomainMismatchException

class Headline(BaseModel):
    title: str = Field(
        default="",
        example="Title of the article",
        description="The title of the article"
    )
    url: AnyHttpUrl | str = Field(
        default="https://example.com",
        example="https://www.example.com",
        description="The URL of the article"
    )


class News(Headline):
    time: str = Field(
        default="",
        example="2021-10-01T00:00:00",
        description="The time the article was published"
    )
    content: str = Field(
        default="",
        example="Content of the article",
        description="The content of the article"
    )


class NewsWithSummary(News):
    summary: str = Field(
        default="",
        example="Summary of the article",
        description="The summary of the article"
    )
    reason: str = Field(
        default="",
        example="Reason of the article",
        description="The reason of the article"
    )


class NewsCrawlerBase(metaclass=abc.ABCMeta):
    """
    Base class for news crawlers.
    Subclasses must provide:
        - news_website_url
        - news_website_news_child_urls
    """
    news_website_url: AnyHttpUrl | str = ""
    news_website_news_child_urls: list[AnyHttpUrl | str] = []

    def get_headline(
        self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:

        headlines: list[Headline] = []
        page_range = range(page[0], page[1] + 1) if isinstance(page, tuple) else [page]

        for p in page_range:
            resp = requests.get(
                f"{self.news_website_url}/search/{search_term}?page={p}", timeout=5
            )
            soup = BeautifulSoup(resp.text, "html.parser")

            for item in soup.select("a"):
                title = item.get_text(strip=True)
                url = item.get("href")

                if title and url:
                    # Normalize relative URLs
                    if url.startswith("/"):
                        url = f"{self.news_website_url.rstrip('/')}{url}"

                    headlines.append(Headline(title=title, url=url))

        return headlines

    def parse(self, url: AnyHttpUrl | str) -> News:
        """Default implementation: extract <h1>, <time>, and all <p> as content."""
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")

        title_el = soup.select_one("h1")
        time_el = soup.select_one("time")

        title = title_el.get_text(strip=True) if title_el else ""
        time = time_el.get_text(strip=True) if time_el else ""
        content = " ".join(p.get_text(strip=True) for p in soup.select("p"))

        return News(title=title, url=url, time=time, content=content)

    def validate_and_parse(self, url: AnyHttpUrl | str) -> News:
        """Validate domain before parsing."""
        if not self._is_valid_url(url):
            raise DomainMismatchException(url)
        return self.parse(url)

    @staticmethod
    def save(news: News, db: Session | None):
        """
        Default save implementation.
        Assumes the caller will convert News → ORM model before saving.
        """
        if db is None:
            return False

        try:
            db.add(news)  # Assumes `news` is ORM-convertible
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    def _is_valid_url(self, url: AnyHttpUrl | str) -> bool:
        main_domain = tldextract.extract(self.news_website_url).registered_domain
        url_domain = tldextract.extract(url).registered_domain
        return url_domain == main_domain
