import asyncio
import hashlib
import logging
import re
from collections import deque
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Crawler:
    """Crawl same-domain HTML pages and save cleaned text documents."""

    def __init__(
        self,
        root_url: str = "https://www.economic.ntpc.gov.tw/",
        output_dir: str = "./data",
        max_depth: int = 2,
        max_pages: Optional[int] = None,
        delay_seconds: float = 2.0,
        timeout: float = 30.0,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
        pause_event: Optional[asyncio.Event] = None,
    ):
        parsed_root = urlparse(root_url)
        if parsed_root.scheme not in {"http", "https"} or not parsed_root.netloc:
            raise ValueError(f"Invalid root URL: {root_url}")
        if max_depth < 0 or (max_pages is not None and max_pages < 1) or delay_seconds < 0:
            raise ValueError("max_depth must be >= 0, max_pages must be None or >= 1, and delay_seconds must be >= 0")

        self.root_url = self._normalize_url(root_url)
        self.domain = parsed_root.netloc.lower()
        self.output_dir = Path(output_dir)
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.progress_callback = progress_callback
        self.pause_event = pause_event
        self.headers = {"User-Agent": "NTPC-Economic-Crawler/1.0"}

    @staticmethod
    def _normalize_url(url: str) -> str:
        normalized, _ = urldefrag(url)
        parsed = urlparse(normalized)
        if parsed.path == "":
            normalized += "/"
        return normalized

    def _is_crawlable_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != self.domain:
            return False
        return not re.search(
            r"\.(?:pdf|docx?|xlsx?|pptx?|zip|rar|7z|jpg|jpeg|png|gif|svg|mp[34]|css|js)(?:$|\?)",
            parsed.path.lower(),
        )

    @staticmethod
    def _extract_page(html: str, url: str) -> Optional[tuple[str, str, list[str]]]:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one(".main-title").get_text(" ", strip=True) if soup.select_one(".main-title") else soup.title.get_text(" ", strip=True) if soup.title else "Untitled"

        content = soup.select_one("#main")
        if content is None:
            return None

        for element in content.select(
            "script, style, noscript, nav, header, footer, aside, form, "
            ".menu, .navbar, .navigation, .breadcrumb, .sidebar, .cookie"
        ):
            element.decompose()

        text = content.get_text(" ", strip=True)
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        cleaned_text = "\n".join(line for line in lines if line)

        links = [
            urljoin(url, anchor["href"])
            for anchor in content.find_all("a", href=True)
            if anchor["href"]
        ]
        return title.strip() or "Untitled", cleaned_text, links

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> Optional[tuple[str, str]]:
        try:
            logger.info("Fetching page: %s", url)
            response = await client.get(url, follow_redirects=True, timeout=self.timeout)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                logger.info("Skipped non-HTML page: %s", url)
                return None
            return str(response.url), response.text
        except httpx.HTTPError as error:
            logger.warning("Could not fetch %s: %s", url, error)
            return None

    async def crawl(self) -> list[dict[str, str]]:
        pages: list[dict[str, str]] = []
        queue = deque([(self.root_url, 0)])
        queued = {self.root_url}
        processed = 0
        logger.info(
            "Crawler started: root=%s, max_pages=%s, max_depth=%s, delay=%ss",
            self.root_url,
            self.max_pages,
            self.max_depth,
            self.delay_seconds,
        )

        async with httpx.AsyncClient(headers=self.headers) as client:
            while queue and (self.max_pages is None or processed < self.max_pages):
                if self.pause_event is not None:
                    await self.pause_event.wait()
                url, depth = queue.popleft()
                fetched = await self._fetch(client, url)
                processed += 1
                if fetched is not None:
                    final_url, html = fetched
                    final_url = self._normalize_url(final_url)
                    links = []
                    extracted = self._extract_page(html, final_url)
                    if extracted is not None:
                        title, text, links = extracted
                        pages.append({"url": final_url, "title": title, "content": text})
                        limit = self.max_pages if self.max_pages is not None else "unlimited"
                        logger.info("Crawled %s/%s: %s", len(pages), limit, final_url)
                    else:
                        logger.info("Skipped page without main#main: %s", final_url)

                    if depth < self.max_depth:
                        for link in links:
                            normalized = self._normalize_url(urljoin(final_url, link))
                            if (
                                normalized not in queued
                                and self._is_crawlable_url(normalized)
                            ):
                                queued.add(normalized)
                                queue.append((normalized, depth + 1))

                    limit = self.max_pages if self.max_pages is not None else "unlimited"
                    logger.info("Queue status: pending=%s, saved=%s/%s", len(queue), len(pages), limit)

                if self.progress_callback:
                    self.progress_callback(processed, len(pages), len(queue))

                if queue and self.delay_seconds:
                    await asyncio.sleep(self.delay_seconds)

        logger.info("Crawler finished: saved=%s pages", len(pages))
        return pages

    def save_pages(self, pages: list[dict[str, str]]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for old_file in self.output_dir.glob("*.txt"):
            old_file.unlink()

        saved_files = []
        for page in pages:
            filename = hashlib.sha1(page["url"].encode("utf-8")).hexdigest()[:12] + ".txt"
            output_file = self.output_dir / filename
            output_file.write_text(
                f"Title: {page['title']}\nURL: {page['url']}\n\n{page['content']}\n",
                encoding="utf-8",
            )
            saved_files.append(output_file)
        logger.info("Saved %s text files to %s", len(saved_files), self.output_dir)
        return saved_files

    async def crawl_and_save(self) -> list[Path]:
        return self.save_pages(await self.crawl())