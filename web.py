import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from logger import logger
from utils import handle_errors, time_it
from typing import List, Dict, Any

class WebIntelligence:
    """Handles real-time web search and page scraping."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @handle_errors("Web")
    @time_it
    def search(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Performs a web search using DuckDuckGo."""
        logger.info(f"Searching the web for: {query}")
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=limit):
                results.append({
                    "title": r["title"],
                    "link": r["href"],
                    "snippet": r["body"]
                })
        return results

    @handle_errors("Web")
    @time_it
    async def scrape_url(self, url: str) -> str:
        """Fetches and extracts readable text from a URL."""
        logger.info(f"Scraping URL: {url}")
        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts, styles, and other non-content elements
            for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
                element.decompose()
            
            # Extract text
            text = soup.get_text(separator=" ", strip=True)
            # Limit to 5000 characters for LLM context
            return text[:5000]

    @handle_errors("Web")
    def get_news(self, topic: str, limit: int = 5) -> List[Dict[str, str]]:
        """Fetches latest news headlines for a specific topic."""
        logger.info(f"Fetching news for: {topic}")
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(topic, max_results=limit):
                results.append({
                    "title": r["title"],
                    "date": r["date"],
                    "source": r["source"],
                    "snippet": r["body"],
                    "link": r["url"]
                })
    @handle_errors("Web")
    @time_it
    def search_images(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Performs an image search using DuckDuckGo."""
        logger.info(f"Searching images for: {query}")
        results = []
        with DDGS() as ddgs:
            for r in ddgs.images(query, max_results=limit):
                results.append({
                    "title": r["title"],
                    "image": r["image"],
                    "thumbnail": r["thumbnail"],
                    "url": r["url"]
                })
        return results
