import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process raw web scraped data for LightRAG ingestion."""

    # Keywords to filter out (boilerplate/navigation)
    GARBAGE_KEYWORDS = {
        "navigation",
        "sidebar",
        "menu",
        "footer",
        "header",
        "advertisement",
        "cookie",
        "skip to content",
        "related links",
        "home",
        "contact us",
        "sitemap",
        "privacy",
        "terms",
    }

    MIN_CONTENT_LENGTH = 100  # Minimum characters for valid document
    CHUNK_SIZE = 300  # Characters per chunk

    @staticmethod
    def _is_garbage(text: str) -> bool:
        """Check if text is mostly garbage/boilerplate."""
        text_lower = text.lower()
        garbage_count = sum(1 for keyword in DataProcessor.GARBAGE_KEYWORDS if keyword in text_lower)
        return garbage_count > len(text) / 200  # More than 1 keyword per 200 chars

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        # Remove unicode control characters
        text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")
        return text.strip()

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        for i in range(0, len(text), chunk_size // 2):  # 50% overlap
            chunk = text[i : i + chunk_size]
            if len(chunk) > 50:  # Minimum chunk size
                chunks.append(chunk)

        return chunks

    @classmethod
    def process_raw_data(
        cls, raw_data: dict, output_dir: Optional[str] = None
    ) -> dict:
        """Process raw scraped data and return cleaned data."""
        cleaned_pages = []
        url_seen = set()

        for page in raw_data.get("pages", []):
            url = page.get("url", "")
            title = cls._clean_text(page.get("title", ""))
            content = cls._clean_text(page.get("content", ""))

            # Deduplication by URL
            if url in url_seen:
                logger.debug(f"Skipping duplicate: {url}")
                continue
            url_seen.add(url)

            # Filter out garbage and short content
            if cls._is_garbage(content):
                logger.debug(f"Skipping garbage content: {url}")
                continue

            if len(content) < cls.MIN_CONTENT_LENGTH:
                logger.debug(f"Skipping short content ({len(content)} chars): {url}")
                continue

            # Chunk content
            chunks = cls._chunk_text(content)

            cleaned_pages.append(
                {
                    "url": url,
                    "title": title,
                    "content": content,
                    "content_length": len(content),
                    "chunk_count": len(chunks),
                    "chunks": chunks,
                    "timestamp": page.get("timestamp"),
                }
            )

            logger.info(f"Processed: {title[:50]}... ({len(content)} chars, {len(chunks)} chunks)")

        logger.info(f"Cleaned {len(cleaned_pages)} documents from {len(raw_data.get('pages', []))} raw pages")

        cleaned_data = {
            "source": raw_data.get("source", ""),
            "processed_timestamp": raw_data.get("timestamp", ""),
            "total_raw_pages": len(raw_data.get("pages", [])),
            "total_cleaned_pages": len(cleaned_pages),
            "pages": cleaned_pages,
        }

        # Save to output directory if specified
        if output_dir:
            cls._save_cleaned_data(cleaned_data, output_dir)

        return cleaned_data

    @classmethod
    def _save_cleaned_data(cls, cleaned_data: dict, output_dir: str) -> None:
        """Save cleaned data to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save cleaned JSON
        json_file = output_path / "ntpc_clean.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved cleaned data to {json_file}")

        # Save individual text files for LightRAG
        docs_dir = output_path / "docs"
        docs_dir.mkdir(exist_ok=True)

        for idx, page in enumerate(cleaned_data["pages"]):
            doc_file = docs_dir / f"doc_{idx}.txt"
            content = f"Title: {page['title']}\nURL: {page['url']}\n\n{page['content']}"
            with open(doc_file, "w", encoding="utf-8") as f:
                f.write(content)

        logger.info(f"Saved {len(cleaned_data['pages'])} documents to {docs_dir}")

    @classmethod
    def load_and_process(
        cls, input_file: str, output_dir: Optional[str] = None
    ) -> dict:
        """Load raw JSON and process it."""
        logger.info(f"Loading raw data from {input_file}")
        with open(input_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        return cls.process_raw_data(raw_data, output_dir)
