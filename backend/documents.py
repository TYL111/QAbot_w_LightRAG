"""Shared discovery of local documents supported by the import pipeline."""

from pathlib import Path

TEXT_SUFFIXES = frozenset({".txt", ".md"})
# Legacy Office requires an explicitly configured, capable MinerU service.
MINERU_SUFFIXES = frozenset({
    ".pdf", ".docx", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg",
    ".jp2", ".webp", ".gif", ".bmp", ".doc", ".ppt", ".xls",
})


def list_document_files(directory: Path, *, include_mineru: bool = False) -> list[Path]:
    """List immediate supported documents, without traversing parser caches."""
    suffixes = TEXT_SUFFIXES | MINERU_SUFFIXES if include_mineru else TEXT_SUFFIXES
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in suffixes
    )
