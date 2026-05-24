import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NTPCEconomicScraper:
    """Web scraper for NTPC Economic Development Bureau website using httpx + BeautifulSoup."""

    def __init__(
        self,
        base_url: str = "https://www.economic.ntpc.gov.tw",
        max_pages: int = 100,
        delay_seconds: float = 1.0,
        timeout: float = 30.0,
    ):
        if not base_url or not base_url.strip():
            raise ValueError("Scraper base_url must be a non-empty URL.")

        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        if not self.domain:
            raise ValueError(f"Invalid scraper base_url: {base_url}")

        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.visited_urls = set()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to absolute form."""
        absolute_url = urljoin(self.base_url, url)
        # Remove fragment
        absolute_url = absolute_url.split("#")[0]
        return absolute_url

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and within domain."""
        if not url:
            return False
        parsed = urlparse(url)
        return parsed.netloc == self.domain

    def _extract_text(self, element) -> str:
        """Extract and clean text from element."""
        if element is None:
            return ""
        text = element.get_text(separator=" ", strip=True)
        return " ".join(text.split())  # Remove extra whitespace

    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Fetch page content via HTTP."""
        try:
            logger.info(f"Fetching: {url}")
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _scrape_page(self, html: str, url: str) -> dict:
        """Parse and extract content from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title_elem = soup.find("title")
            title = self._extract_text(title_elem) if title_elem else "Untitled"
            if not title:
                title = "Untitled"

            # Extract main content
            content = ""
            selectors = [
                "main",
                ".content",
                ".main-content",
                "article",
                ".article-content",
                "#content",
            ]
            for selector in selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self._extract_text(content_elem)
                    if len(content) > 100:
                        break

            # Fallback to body if no specific content found
            if len(content) < 100:
                body_elem = soup.find("body")
                if body_elem:
                    content = self._extract_text(body_elem)

            # Extract links for BFS crawling
            links = []
            for link_elem in soup.find_all("a", href=True):
                href = link_elem["href"]
                if "/News/Page" in href:
                    normalized = self._normalize_url(href)
                    if self._is_valid_url(normalized) and normalized not in self.visited_urls:
                        links.append(normalized)

            return {
                "url": url,
                "title": title,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "links": list(set(links))[:10],  # Limit to 10 unique links
            }

        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None

    async def scrape(self) -> list[dict]:
        """Perform BFS-based crawling of the website."""
        logger.info(f"Starting scrape of {self.base_url}")

        pages = []
        queue = deque([self.base_url])
        self.visited_urls.add(self.base_url)

        async with httpx.AsyncClient(headers=self.headers) as client:
            while queue and len(pages) < self.max_pages:
                url = queue.popleft()

                # Fetch and parse the page
                html = await self._fetch_page(client, url)
                if html:
                    page_data = self._scrape_page(html, url)
                    if page_data:
                        pages.append(page_data)
                        logger.info(f"Scraped {len(pages)}/{self.max_pages} pages")

                        # Add new links to queue
                        for link in page_data.get("links", []):
                            if (
                                link not in self.visited_urls
                                and len(self.visited_urls) < self.max_pages
                            ):
                                queue.append(link)
                                self.visited_urls.add(link)

                # Rate limiting
                await asyncio.sleep(self.delay_seconds)

        logger.info(f"Scraping completed. Total pages: {len(pages)}")
        return pages

    async def scrape_and_save(self, output_file: str) -> str:
        """Scrape website and save to JSON file."""
        pages = await self.scrape()

        output_data = {
            "source": self.base_url or "unknown",
            "timestamp": datetime.now().isoformat(),
            "total_pages": len(pages),
            "pages": pages,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(pages)} pages to {output_file}")
        return output_file
