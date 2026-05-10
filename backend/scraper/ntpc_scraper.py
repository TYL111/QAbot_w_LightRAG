import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse
from collections import deque

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class NTPCEconomicScraper:
    """Web scraper for NTPC Economic Development Bureau website."""

    def __init__(
        self,
        base_url: str = "https://www.economic.ntpc.gov.tw",
        max_pages: int = 100,
        delay_seconds: float = 2.0,
        headless: bool = True,
    ):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.headless = headless
        self.visited_urls = set()
        self.driver: Optional[webdriver.Chrome] = None

    def _setup_driver(self) -> webdriver.Chrome:
        """Initialize Selenium WebDriver with Chrome options."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        return webdriver.Chrome(options=options)

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
        try:
            text = element.get_attribute("textContent") or ""
            return " ".join(text.split())  # Remove extra whitespace
        except Exception:
            return ""

    def _scrape_page(self, url: str) -> dict:
        """Scrape content from a single page."""
        try:
            logger.info(f"Scraping: {url}")
            self.driver.get(url)

            # Wait for content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning(f"Timeout loading: {url}")
                return None

            # Extract title
            title = ""
            try:
                title_elem = self.driver.find_element(
                    By.CSS_SELECTOR, "h1, .page-title, .title"
                )
                title = self._extract_text(title_elem)
            except NoSuchElementException:
                title = self.driver.title

            # Extract main content
            content = ""
            try:
                # Try common content containers
                selectors = [
                    "main",
                    ".content",
                    ".main-content",
                    "article",
                    ".article-content",
                    "#content",
                ]
                for selector in selectors:
                    try:
                        content_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        content = self._extract_text(content_elem)
                        if len(content) > 100:
                            break
                    except NoSuchElementException:
                        continue

                # Fallback to body if no specific content found
                if len(content) < 100:
                    body_elem = self.driver.find_element(By.TAG_NAME, "body")
                    content = self._extract_text(body_elem)
            except Exception as e:
                logger.warning(f"Error extracting content from {url}: {e}")

            # Extract links for BFS crawling
            links = []
            try:
                link_elements = self.driver.find_elements(By.TAG_NAME, "a")
                for link_elem in link_elements:
                    href = link_elem.get_attribute("href")
                    if href:
                        normalized = self._normalize_url(href)
                        if self._is_valid_url(normalized) and normalized not in self.visited_urls:
                            links.append(normalized)
            except Exception as e:
                logger.warning(f"Error extracting links from {url}: {e}")

            return {
                "url": url,
                "title": title,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "links": list(set(links))[:10],  # Limit to 10 unique links
            }

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    async def scrape(self) -> list[dict]:
        """Perform BFS-based crawling of the website."""
        logger.info(f"Starting scrape of {self.base_url}")

        self.driver = self._setup_driver()
        pages = []
        queue = deque([self.base_url])
        self.visited_urls.add(self.base_url)

        try:
            while queue and len(pages) < self.max_pages:
                url = queue.popleft()

                # Scrape the page
                page_data = self._scrape_page(url)
                if page_data:
                    pages.append(page_data)
                    logger.info(f"Scraped {len(pages)}/{self.max_pages} pages")

                    # Add new links to queue
                    for link in page_data.get("links", []):
                        if link not in self.visited_urls and len(self.visited_urls) < self.max_pages:
                            queue.append(link)
                            self.visited_urls.add(link)

                # Rate limiting
                await asyncio.sleep(self.delay_seconds)

        finally:
            if self.driver:
                self.driver.quit()

        logger.info(f"Scraping completed. Total pages: {len(pages)}")
        return pages

    async def scrape_and_save(self, output_file: str) -> str:
        """Scrape website and save to JSON file."""
        pages = await self.scrape()

        output_data = {
            "source": self.base_url,
            "timestamp": datetime.now().isoformat(),
            "total_pages": len(pages),
            "pages": pages,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(pages)} pages to {output_file}")
        return output_file
