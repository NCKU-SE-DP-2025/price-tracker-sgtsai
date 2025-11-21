import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from requests.models import Response

from app.crawler.crawler_base import NewsCrawlerBase, Headline, News
from app.crawler.exceptions import DomainMismatchException
from app.crawler.udn_crawler import UDNCrawler


class DummyCrawler(NewsCrawlerBase):
    def __init__(self):
        self.news_website_url = "https://example.com"


def make_response(text: str, json_data: dict | None = None) -> Response:
    resp = Response()
    resp._content = text.encode("utf-8")
    resp.status_code = 200
    if json_data is not None:
        # monkeypatch .json()
        resp.json = lambda: json_data
    return resp


def test_is_valid_url_passes_and_fails():
    crawler = DummyCrawler()
    assert crawler._is_valid_url("https://example.com/news/123")
    assert not crawler._is_valid_url("https://other.com/news/123")


def test_validate_and_parse_raises_on_domain_mismatch():
    crawler = DummyCrawler()
    with pytest.raises(DomainMismatchException):
        crawler.validate_and_parse("https://other.com/news/123")


@patch("app.crawler.crawler_base.requests.get")
def test_get_headline_parses_links(mock_get):
    html = """
    <html><body>
      <a href="/article1">First Article</a>
      <a href="https://example.com/article2">Second Article</a>
    </body></html>
    """
    mock_get.return_value = make_response(html)
    crawler = DummyCrawler()
    headlines = crawler.get_headline("term", page=1)
    assert len(headlines) == 2
    assert headlines[0].title == "First Article"
    assert headlines[0].url.startswith("https://example.com")


@patch("app.crawler.crawler_base.requests.get")
def test_parse_extracts_title_time_content(mock_get):
    html = """
    <html><body>
      <h1>My Title</h1>
      <time>2021-10-01</time>
      <p>Paragraph one.</p><p>Paragraph two.</p>
    </body></html>
    """
    mock_get.return_value = make_response(html)
    crawler = DummyCrawler()
    news = crawler.parse("https://example.com/article")
    assert isinstance(news, News)
    assert "My Title" in news.title
    assert "Paragraph one." in news.content


@patch("app.crawler.udn_crawler.requests.get")
def test_udn_parse_headlines_from_json(mock_get):
    json_data = {
        "lists": [
            {"title": "UDN Title", "url": "https://udn.com/news/1"},
            {"title": "Alt Title", "titleLink": "https://udn.com/news/2"},
        ]
    }
    mock_get.return_value = make_response("{}", json_data=json_data)
    crawler = UDNCrawler()
    headlines = crawler.get_headline("searchterm", page=1)
    assert len(headlines) == 2
    assert headlines[0].title == "UDN Title"


@patch("app.crawler.udn_crawler.requests.get")
def test_udn_parse_article_html(mock_get):
    html = """
    <html><body>
      <h1 class="article-content__title">UDN News</h1>
      <time class="article-content__time">2021-11-01</time>
      <div class="article-content__editor">
        <p>Content A</p><p>Content B</p>
      </div>
    </body></html>
    """
    mock_get.return_value = make_response(html)
    crawler = UDNCrawler()
    news = crawler.parse("https://udn.com/news/123")
    assert "UDN News" in news.title
    assert "Content A" in news.content


def test_save_commits_and_rolls_back():
    crawler = DummyCrawler()
    mock_db = MagicMock()
    news = News(title="t", url="u", time="now", content="c")

    # success path
    assert crawler.save(news, mock_db)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

    # failure path
    mock_db.reset_mock()
    def fail_commit(): raise Exception("fail")
    mock_db.commit.side_effect = fail_commit
    result = crawler.save(news, mock_db)
    assert result is False
    mock_db.rollback.assert_called_once()
