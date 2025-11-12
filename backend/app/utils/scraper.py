import requests
from bs4 import BeautifulSoup

class ScraperUtil:
    @staticmethod
    def fetch_article_content(url: str) -> dict:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("h1", class_="article-content__title").text.strip()
        time = soup.find("time", class_="article-content__time").text.strip()
        section = soup.find("section", class_="article-content__editor")
        paragraphs = [p.text.strip() for p in section.find_all("p") if p.text.strip() and "▪" not in p.text]
        return {"url": url, "title": title, "time": time, "content": paragraphs}
