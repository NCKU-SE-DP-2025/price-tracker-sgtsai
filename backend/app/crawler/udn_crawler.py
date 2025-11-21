"""
UDN News Scraper Module

Concrete implementation of NewsCrawlerBase for UDN.
"""

import requests
from requests import Response
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from .crawler_base import NewsCrawlerBase, Headline, News, NewsWithSummary


class UDNCrawler(NewsCrawlerBase):
    CHANNEL_ID = 2

    def __init__(self, timeout: int = 5) -> None:
        # UDN API endpoint for "more" news
        self.news_website_url = "https://udn.com/api/more"
        self.timeout = timeout

    def startup(self, search_term: str) -> list[Headline]:
        """
        Convenience method: fetch headlines from the first 10 pages.
        """
        return self.get_headline(search_term, page=(1, 10))

    def get_headline(
        self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:
        """
        Fetch headlines for a given search term and page(s).
        """
        page_range = (
            range(page[0], page[1] + 1) if isinstance(page, tuple) else [page]
        )
        headlines: list[Headline] = []
        for p in page_range:
            headlines.extend(self._fetch_news(p, search_term))
        return headlines

    def _fetch_news(self, page: int, search_term: str) -> list[Headline]:
        """
        Internal helper: perform API request and parse headlines.
        """
        params = self._create_search_params(page, search_term)
        resp = self._perform_request(params=params)
        return self._parse_headlines(resp)

    def _create_search_params(self, page: int, search_term: str) -> dict:
        """
        Build query parameters for UDN API.
        """
        return {
            "channelId": self.CHANNEL_ID,
            "page": page,
            "id": f"search:{search_term}",  # required by UDN API
        }

    def _perform_request(
        self, url: str | None = None, params: dict | None = None
    ) -> Response:
        """
        Perform GET request to UDN API.
        """
        return requests.get(
            url or self.news_website_url, params=params, timeout=self.timeout
        )

    @staticmethod
    def _parse_headlines(response: Response) -> list[Headline]:
        """
        Parse API JSON response into Headline objects.
        """
        data = response.json()
        headlines: list[Headline] = []
        for item in data.get("lists", []):
            # UDN API sometimes uses "titleLink" instead of "url"
            url = item.get("url") or item.get("titleLink", "")
            headlines.append(
                Headline(title=item.get("title", ""), url=url)
            )
        return headlines

    def parse(self, url: str) -> News:
        """
        Fetch and parse a single news article page.
        """
        resp = requests.get(url, timeout=self.timeout)
        soup = BeautifulSoup(resp.text, "html.parser")
        return self._extract_news(soup, url)

    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
        """
        Extract title, time, and content from article HTML.
        """
        title_el = soup.select_one("h1.article-content__title") or soup.select_one("h1")
        time_el = soup.select_one("time.article-content__time") or soup.select_one(".article-time")
        content_el = soup.select(".article-content__editor p") or soup.select(".article-content p")

        title = title_el.get_text(strip=True) if title_el else ""
        time = time_el.get_text(strip=True) if time_el else ""
        content = " ".join(p.get_text(strip=True) for p in content_el)

        return News(title=title, url=url, time=time, content=content)

    def save(self, news: NewsWithSummary, db: Session):
        """
        Save NewsWithSummary into database.
        """
        db.add(news)
        self._commit_changes(db)

    @staticmethod
    def _commit_changes(db: Session):
        """
        Commit DB transaction safely.
        """
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
