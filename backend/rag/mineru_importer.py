"""Enqueue binary documents into LightRAG's own MinerU/sidecar pipeline."""

import asyncio
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import httpx
from lightrag.base import DocStatus
from lightrag.constants import FULL_DOCS_FORMAT_PENDING_PARSE
from lightrag.parser.registry import suffix_capabilities
from lightrag.utils import compute_mdhash_id

from backend.config import Settings


class MinerUImporter:
    def __init__(self, config: Settings):
        self.config = config

    def configure(self) -> None:
        """Configure the env-based built-in adapter once for this API process."""
        if not self.config.mineru_enabled:
            return
        for name in (
            "mineru_api_mode", "mineru_local_endpoint", "mineru_official_endpoint",
            "mineru_additional_suffixes", "mineru_language", "mineru_local_backend",
            "mineru_local_parse_method", "mineru_enable_table", "mineru_enable_formula",
        ):
            value = getattr(self.config, name)
            os.environ[name.upper()] = str(value).lower() if isinstance(value, bool) else value
        os.environ["MINERU_API_TOKEN"] = self.config.mineru_api_token.get_secret_value()
        os.environ["INPUT_DIR"] = str(Path(self.config.mineru_input_dir).resolve())

    def validate(self, paths: list[Path]) -> None:
        if not self.config.mineru_enabled:
            raise ValueError("Set MINERU_ENABLED=true to import binary documents.")
        if self.config.mineru_api_mode == "official":
            if not self.config.mineru_api_token.get_secret_value().strip():
                raise ValueError("Set MINERU_API_TOKEN for official MinerU parsing.")
        elif not self.config.mineru_local_endpoint.strip():
            raise ValueError("Set MINERU_LOCAL_ENDPOINT to a compatible MinerU service.")
        supported = suffix_capabilities("mineru")
        for path in paths:
            if path.suffix.lower().lstrip(".") not in supported:
                raise ValueError(
                    f"MinerU does not advertise {path.suffix}: {path.name}. "
                    "For legacy .doc/.ppt/.xls, first verify the service supports it, "
                    "then add its suffix to MINERU_ADDITIONAL_SUFFIXES."
                )

    def _stage(self, source: Path) -> Path:
        """Use path+content identity; keep the original when LightRAG archives."""
        source = source.resolve()
        content_hash = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                content_hash.update(chunk)
        path_hash = hashlib.sha256(os.path.normcase(str(source)).encode()).hexdigest()[:12]
        stem = re.sub(r"[^\w .-]", "_", source.stem)[:80]
        filename = f"{path_hash}-{content_hash.hexdigest()[:12]}-{stem}{source.suffix.lower()}"
        directory = Path(self.config.mineru_input_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        staged = directory / filename
        if not staged.exists():
            shutil.copy2(source, staged)
        # Provenance stays available even after LightRAG archives the copy.
        staged.with_suffix(staged.suffix + ".source.json").write_text(
            json.dumps({"original_path": str(source), "file_name": source.name,
                        "sha256": content_hash.hexdigest()}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return staged

    async def _check_local_service(self) -> None:
        """Reject a down/incompatible local API before persisting pending jobs."""
        if self.config.mineru_api_mode != "local":
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    self.config.mineru_local_endpoint.rstrip("/") + "/openapi.json",
                )
                response.raise_for_status()
                paths = response.json().get("paths", {})
        except (httpx.HTTPError, ValueError, AttributeError) as error:
            raise RuntimeError(
                "MinerU service is unavailable or has no valid /openapi.json. "
                "Check MINERU_LOCAL_ENDPOINT and start a compatible service."
            ) from error
        if "/tasks" not in paths or not any(
            re.fullmatch(r"/tasks/\{[^}]+\}/result", path) for path in paths
        ):
            raise RuntimeError(
                "This LightRAG version requires the MinerU /tasks and "
                "/tasks/{task_id}/result API. A MinerU 4.x /v1-only service "
                "cannot be used directly; use a compatible service or official mode."
            )

    async def insert(self, rag, paths: list[Path]) -> None:
        self.validate(paths)
        pending = []
        staged_documents = []
        for source in paths:
            staged = await asyncio.to_thread(self._stage, source)
            doc_id = compute_mdhash_id(staged.name, prefix="doc-")
            staged_documents.append((source, doc_id))
            existing = await rag.doc_status.get_by_id(doc_id)
            if existing:
                status = existing.get("status")
                if status == DocStatus.PROCESSED:
                    continue
                if status == DocStatus.FAILED:
                    raise RuntimeError(
                        f"Previous MinerU import failed for {source.name} ({doc_id}): "
                        f"{existing.get('error_msg') or 'unknown error'}. "
                        "Fix the parser service and retry this failed document using "
                        "LightRAG's retry workflow; refresh does not erase failed records."
                    )
                # Already queued/interrupted: let the native pipeline resume it.
            else:
                pending.append(str(staged))
        if pending:
            await self._check_local_service()
            # Do not supply ids: LightRAG treats explicit ids as RAW text inserts.
            await rag.apipeline_enqueue_documents(
                [""] * len(pending), file_paths=pending,
                docs_format=FULL_DOCS_FORMAT_PENDING_PARSE,
                parse_engine="mineru", process_options="P",
            )
        await rag.apipeline_process_enqueue_documents()
        # The native pipeline persists per-file failures rather than raising.
        # Surface them so /refresh/status does not incorrectly report success.
        for source, doc_id in staged_documents:
            result = await rag.doc_status.get_by_id(doc_id)
            if not result or result.get("status") != DocStatus.PROCESSED:
                detail = (result or {}).get("error_msg") or (result or {}).get("status")
                raise RuntimeError(f"MinerU import incomplete for {source.name}: {detail}")
