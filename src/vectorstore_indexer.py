import hashlib
import json
import logging
import multiprocessing
import os
import gc
import queue
import shutil
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

try:
    from .config import CHROMA_PATH, DATA_PATH, EMBEDDING_MODEL_NAME
    from .data_loader import clear_cached_chroma, get_embedding_function
except ImportError:
    from config import CHROMA_PATH, DATA_PATH, EMBEDDING_MODEL_NAME
    from data_loader import clear_cached_chroma, get_embedding_function

from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)
MANIFEST_FILENAME = "index_manifest.json"
INDEX_VERSION = 2
DEFAULT_BATCH_SIZE = 32
INDEX_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "length_function": "len",
    "add_start_index": True,
}


def _ensure_numpy_compat() -> None:
    """Allow the pinned ChromaDB release to run with NumPy 2.x."""
    import numpy as np

    if not hasattr(np, "float_"):
        np.float_ = np.float64
    if not hasattr(np, "NaN"):
        np.NaN = np.nan


def _now() -> float:
    return time.perf_counter()


class _TimedEmbeddings:
    def __init__(self, embeddings: Any, timings: Dict[str, float]):
        self._embeddings = embeddings
        self._timings = timings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        started = _now()
        values = self._embeddings.embed_documents(texts)
        self._timings["embedding"] = self._timings.get("embedding", 0.0) + (_now() - started)
        return values

    def embed_query(self, text: str) -> List[float]:
        return self._embeddings.embed_query(text)


def _hash_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_path(path: str, data_path: str) -> str:
    return os.path.relpath(path, data_path).replace(os.sep, "/")


def _discover_files(data_path: str) -> List[Tuple[str, str]]:
    files = []
    for root, _, names in os.walk(data_path):
        for name in names:
            if os.path.splitext(name)[1].lower() not in {".pdf", ".txt"}:
                continue
            path = os.path.join(root, name)
            files.append((_source_path(path, data_path), path))
    return sorted(files)


def _load_file(path: str, source: str, fingerprint: str) -> List[Document]:
    if path.lower().endswith(".pdf"):
        documents = PyPDFLoader(path).load()
    else:
        documents = TextLoader(path, encoding="utf-8").load()

    for document in documents:
        document.metadata.update({
            "source_file": source,
            "source_hash": fingerprint,
        })
    return documents


def _split(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=INDEX_CONFIG["chunk_size"],
        chunk_overlap=INDEX_CONFIG["chunk_overlap"],
        length_function=len,
        add_start_index=INDEX_CONFIG["add_start_index"],
    )
    return splitter.split_documents(documents)


def _chunk_id(source: str, fingerprint: str, index: int) -> str:
    stable_source = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"{stable_source}:{fingerprint[:16]}:{index}"


def _chunks_for_source(source: str, fingerprint: str, documents: List[Document]) -> Tuple[List[Document], List[str]]:
    chunks = _split(documents)
    ids = []
    for index, chunk in enumerate(chunks):
        chunk.metadata.update({
            "source_file": source,
            "source_hash": fingerprint,
            "chunk_index": index,
        })
        ids.append(_chunk_id(source, fingerprint, index))
    return chunks, ids


def _manifest_path(chroma_path: str) -> str:
    return os.path.join(chroma_path, MANIFEST_FILENAME)


def _read_manifest(chroma_path: str) -> Dict[str, Any]:
    path = _manifest_path(chroma_path)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as manifest_file:
            value = json.load(manifest_file)
    except (OSError, ValueError):
        logger.warning("Ignoring unreadable index manifest at %s", path)
        return {}
    return value if isinstance(value, dict) else {}


def _write_manifest(chroma_path: str, manifest: Dict[str, Any]) -> None:
    os.makedirs(chroma_path, exist_ok=True)
    target = _manifest_path(chroma_path)
    temporary = f"{target}.{uuid.uuid4().hex}.tmp"
    with open(temporary, "w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2, sort_keys=True)
        manifest_file.flush()
        os.fsync(manifest_file.fileno())
    os.replace(temporary, target)


def _batches(items: List[Any], size: int = DEFAULT_BATCH_SIZE) -> Iterable[List[Any]]:
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _open_store(path: str, embeddings: Any) -> Chroma:
    _ensure_numpy_compat()
    return Chroma(persist_directory=path, embedding_function=embeddings)


def _add_batches(store: Chroma, chunks: List[Document], ids: List[str]) -> None:
    for chunk_batch, id_batch in zip(_batches(chunks), _batches(ids)):
        store.add_documents(chunk_batch, ids=id_batch)


def _new_manifest(
    files: Dict[str, Dict[str, Any]],
    timings: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    return {
        "version": INDEX_VERSION,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "index_config": INDEX_CONFIG,
        "files": files,
        "metadata": {
            "file_count": len(files),
            "document_count": sum(int(info.get("documents", 0)) for info in files.values()),
            "chunk_count": sum(int(info.get("chunks", 0)) for info in files.values()),
        },
        "timings": dict(timings or {}),
    }


def _safe_replace_directory(source: str, target: str) -> None:
    backup = f"{target}.backup-{uuid.uuid4().hex}"
    moved_target = False
    logger.info(
        "Preparing vector store publication: source=%s exists=%s directory=%s; "
        "target=%s exists=%s directory=%s",
        source,
        os.path.exists(source),
        os.path.isdir(source),
        target,
        os.path.exists(target),
        os.path.isdir(target),
    )
    try:
        if os.path.exists(target):
            os.rename(target, backup)
            moved_target = True
    except OSError as error:
        logger.error(
            "Could not move live vector store aside: target=%s winerror=%s "
            "errno=%s source_exists=%s target_exists=%s",
            target,
            getattr(error, "winerror", None),
            getattr(error, "errno", None),
            os.path.exists(source),
            os.path.exists(target),
            exc_info=True,
        )
        raise RuntimeError(
            f"Unable to move the existing vector store '{target}' aside before "
            f"publishing '{source}'. The existing store was preserved: {error}"
        ) from error

    try:
        os.replace(source, target)
    except OSError as error:
        logger.error(
            "Could not publish staged vector store: source=%s exists=%s directory=%s "
            "target=%s exists=%s backup=%s exists=%s winerror=%s errno=%s",
            source,
            os.path.exists(source),
            os.path.isdir(source),
            target,
            os.path.exists(target),
            backup,
            os.path.exists(backup),
            getattr(error, "winerror", None),
            getattr(error, "errno", None),
            exc_info=True,
        )
        if moved_target and os.path.exists(backup):
            try:
                os.rename(backup, target)
            except OSError as restore_error:
                raise RuntimeError(
                    f"Unable to publish the rebuilt vector store '{source}', and "
                    f"restoring the existing store '{target}' also failed. The "
                    f"backup remains at '{backup}': {restore_error}"
                ) from error
        raise RuntimeError(
            f"Unable to publish the rebuilt vector store '{source}' to '{target}'. "
            f"The existing store was preserved: {error}"
        ) from error

    if moved_target:
        try:
            shutil.rmtree(backup)
        except OSError:
            logger.warning(
                "Published vector store at %s, but could not remove backup %s",
                target,
                backup,
                exc_info=True,
            )


def _prepare_sources(data_path: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, float], int]:
    started = _now()
    discovered = _discover_files(data_path)
    discovery_seconds = _now() - started
    sources = {}
    for source, path in discovered:
        sources[source] = {
            "path": path,
            "hash": _hash_file(path),
        }
    return sources, {"discovery": discovery_seconds, "hashing": _now() - started - discovery_seconds}, len(discovered)


def _prepare_chunks(
    sources: Dict[str, Dict[str, Any]],
    previous_files: Dict[str, Dict[str, Any]],
) -> Tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, List[Document]],
    Dict[str, List[str]],
    Dict[str, float],
    int,
    int,
]:
    started = _now()
    prepared = {}
    chunks_by_source = {}
    ids_by_source = {}
    readable_files = 0
    readable_documents = 0
    parsing_total = 0.0
    chunking_total = 0.0
    for source, info in sources.items():
        try:
            parsing_started = _now()
            documents = _load_file(info["path"], source, info["hash"])
            if not documents:
                raise ValueError("no readable content")
            parsing_total += _now() - parsing_started
            chunk_started = _now()
            chunks, ids = _chunks_for_source(source, info["hash"], documents)
            chunking_total += _now() - chunk_started
            prepared[source] = {
                "hash": info["hash"],
                "chunks": len(chunks),
                "ids": ids,
                "documents": len(documents),
            }
            chunks_by_source[source] = chunks
            ids_by_source[source] = ids
            readable_files += 1
            readable_documents += len(documents)
        except Exception as error:
            raise RuntimeError(f"Failed to parse source file '{source}': {error}") from error
    elapsed = _now() - started
    return (
        prepared,
        chunks_by_source,
        ids_by_source,
        {
            "parsing": parsing_total,
            "chunking": chunking_total,
            "parsing_and_chunking": elapsed,
        },
        readable_files,
        readable_documents,
    )


def _build_full(
    chroma_path: str,
    prepared: Dict[str, Dict[str, Any]],
    chunks_by_source: Dict[str, List[Document]],
    ids_by_source: Dict[str, List[str]],
    timings: Dict[str, float],
) -> None:
    parent = os.path.dirname(os.path.abspath(chroma_path)) or "."
    temp_path = os.path.join(parent, f".{os.path.basename(chroma_path)}.staging-{uuid.uuid4().hex}")
    os.makedirs(temp_path)
    try:
        if os.name == "nt" and _open_store is _ORIGINAL_OPEN_STORE:
            _build_full_in_worker(
                temp_path,
                prepared,
                chunks_by_source,
                ids_by_source,
                timings,
            )
        else:
            _populate_full_store(
                temp_path,
                prepared,
                chunks_by_source,
                ids_by_source,
                timings,
            )
        logger.info(
            "Full rebuild completed before publication: staging=%s exists=%s "
            "directory=%s",
            temp_path,
            os.path.exists(temp_path),
            os.path.isdir(temp_path),
        )
        clear_cached_chroma()
        _safe_replace_directory(temp_path, chroma_path)
    except Exception:
        shutil.rmtree(temp_path, ignore_errors=True)
        raise


def _populate_full_store(
    temp_path: str,
    prepared: Dict[str, Dict[str, Any]],
    chunks_by_source: Dict[str, List[Document]],
    ids_by_source: Dict[str, List[str]],
    timings: Dict[str, float],
) -> None:
    embedding_timings: Dict[str, float] = {}
    store = None
    try:
        embeddings = _TimedEmbeddings(get_embedding_function(), embedding_timings)
        store = _open_store(temp_path, embeddings)
        writes_started = _now()
        for source in sorted(chunks_by_source):
            _add_batches(store, chunks_by_source[source], ids_by_source[source])
        timings["embedding"] = embedding_timings.get("embedding", 0.0)
        timings["embedding_and_writes"] = _now() - writes_started
        timings["database_writes"] = max(
            0.0, timings["embedding_and_writes"] - timings["embedding"]
        )
        _write_manifest(temp_path, _new_manifest(prepared, timings))
        _close_store(store)
        store = None
    except Exception:
        try:
            _close_store(store)
        except Exception:
            logger.exception("Failed to close staged vector store")
        raise


def _full_build_worker(
    temp_path: str,
    prepared: Dict[str, Dict[str, Any]],
    chunks_by_source: Dict[str, List[Document]],
    ids_by_source: Dict[str, List[str]],
    timings: Dict[str, float],
    result_queue: Any,
) -> None:
    try:
        _populate_full_store(
            temp_path,
            prepared,
            chunks_by_source,
            ids_by_source,
            timings,
        )
        result_queue.put(("ok", timings))
    except Exception as error:
        logger.exception("Full rebuild worker failed")
        result_queue.put(("error", repr(error)))
        raise


def _build_full_in_worker(
    temp_path: str,
    prepared: Dict[str, Dict[str, Any]],
    chunks_by_source: Dict[str, List[Document]],
    ids_by_source: Dict[str, List[str]],
    timings: Dict[str, float],
) -> None:
    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    worker = context.Process(
        target=_full_build_worker,
        args=(
            temp_path,
            prepared,
            chunks_by_source,
            ids_by_source,
            timings,
            result_queue,
        ),
        name="vectorstore-full-build",
    )
    worker.start()
    worker.join()
    logger.info(
        "Full rebuild worker exited: pid=%s exitcode=%s staging_exists=%s",
        worker.pid,
        worker.exitcode,
        os.path.exists(temp_path),
    )
    try:
        result = result_queue.get(timeout=5)
    except queue.Empty:
        result = None
    result_queue.close()
    result_queue.join_thread()
    if worker.exitcode != 0:
        detail = result[1] if result and result[0] == "error" else "no worker error was reported"
        raise RuntimeError(
            f"Full rebuild worker exited with code {worker.exitcode}: {detail}"
        )
    if not result or result[0] != "ok":
        raise RuntimeError("Full rebuild worker exited without completing the staged store")
    timings.update(result[1])


def _close_store(store: Any) -> None:
    if store is None:
        return
    client = getattr(store, "_client", None)
    system = getattr(client, "_system", None)
    logger.info(
        "Closing Chroma client: store_type=%s client_type=%s system_type=%s",
        type(store).__name__,
        type(client).__name__ if client is not None else None,
        type(system).__name__ if system is not None else None,
    )
    if system is not None and hasattr(system, "stop"):
        system.stop()
    del store
    gc.collect()


_ORIGINAL_OPEN_STORE = _open_store


def _manifest_compatible(manifest: Dict[str, Any]) -> bool:
    files = manifest.get("files")
    if (
        manifest.get("version") != INDEX_VERSION
        or manifest.get("embedding_model") != EMBEDDING_MODEL_NAME
        or manifest.get("index_config") != INDEX_CONFIG
        or not isinstance(files, dict)
    ):
        return False
    try:
        return all(
            isinstance(info, dict)
            and isinstance(info.get("hash"), str)
            and isinstance(info.get("ids"), list)
            and int(info.get("chunks", -1)) == len(info["ids"])
            and int(info.get("documents", -1)) >= 0
            for info in files.values()
        )
    except (TypeError, ValueError):
        return False


def _stage_existing_store(chroma_path: str) -> str:
    parent = os.path.dirname(os.path.abspath(chroma_path)) or "."
    staged_path = os.path.join(parent, f".{os.path.basename(chroma_path)}.staging-{uuid.uuid4().hex}")
    try:
        shutil.copytree(chroma_path, staged_path)
    except Exception:
        shutil.rmtree(staged_path, ignore_errors=True)
        raise
    return staged_path


def index_documents(data_path: str = DATA_PATH, chroma_path: str = CHROMA_PATH, full: bool = False) -> Dict[str, Any]:
    started = _now()
    if not os.path.isdir(data_path):
        raise ValueError("No documents found in data folder to index.")

    sources, timings, discovered_files = _prepare_sources(data_path)
    if not sources:
        raise ValueError("No documents found in data folder to index.")

    previous_manifest = _read_manifest(chroma_path) if os.path.isdir(chroma_path) else {}
    previous_files = previous_manifest.get("files", {}) if isinstance(previous_manifest, dict) else {}
    incremental = (
        not full
        and os.path.isdir(chroma_path)
        and _manifest_compatible(previous_manifest)
    )
    unchanged = {
        source for source, info in sources.items()
        if incremental and previous_files.get(source, {}).get("hash") == info["hash"]
    }
    sources_to_prepare = {
        source: info for source, info in sources.items() if source not in unchanged
    }
    (
        changed_prepared,
        chunks_by_source,
        ids_by_source,
        preparation_timings,
        changed_readable_files,
        changed_readable_documents,
    ) = _prepare_chunks(sources_to_prepare, previous_files)
    timings.update(preparation_timings)
    prepared = (
        {**previous_files, **changed_prepared}
        if incremental
        else changed_prepared
    )
    if incremental:
        for source in set(previous_files) - set(sources):
            prepared.pop(source, None)
    readable_files = len(sources) if incremental else changed_readable_files
    readable_documents = (
        sum(int(previous_files[source].get("documents", 0)) for source in unchanged)
        + changed_readable_documents
        if incremental
        else changed_readable_documents
    )
    new_files = set(prepared) - set(previous_files)
    modified_files = {
        source for source in prepared
        if source not in unchanged and source in previous_files
    }
    deleted_files = set(previous_files) - set(prepared) if incremental else set()

    if not incremental:
        _build_full(chroma_path, prepared, chunks_by_source, ids_by_source, timings)
        indexed_files = len(prepared)
        skipped_files = 0
    else:
        changed = sorted(new_files | modified_files)
        started_writes = _now()
        if changed or deleted_files:
            embedding_timings: Dict[str, float] = {}
            staged_path = None
            store = None
            try:
                # Chroma has no transaction spanning adds, deletes, and the
                # manifest. Work on a sibling copy and publish it only after
                # every operation succeeds, leaving the live store recoverable
                # if embedding or persistence fails.
                staged_path = _stage_existing_store(chroma_path)
                embeddings = (
                    _TimedEmbeddings(get_embedding_function(), embedding_timings)
                    if changed
                    else None
                )
                store = _open_store(staged_path, embeddings)
                for source in changed:
                    _add_batches(store, chunks_by_source[source], ids_by_source[source])
                old_ids = [
                    chunk_id
                    for source in sorted(modified_files | deleted_files)
                    for chunk_id in previous_files[source].get("ids", [])
                ]
                if old_ids:
                    store.delete(ids=old_ids)
                timings["embedding_and_writes"] = _now() - started_writes
                timings["embedding"] = embedding_timings.get("embedding", 0.0)
                timings["database_writes"] = max(
                    0.0,
                    timings["embedding_and_writes"] - timings["embedding"],
                )
                _write_manifest(staged_path, _new_manifest(prepared, timings))
                _close_store(store)
                store = None
                clear_cached_chroma()
                _safe_replace_directory(staged_path, chroma_path)
                staged_path = None
            except Exception:
                _close_store(store)
                if staged_path:
                    shutil.rmtree(staged_path, ignore_errors=True)
                raise
        else:
            timings["embedding_and_writes"] = 0.0
            timings["embedding"] = 0.0
            timings["database_writes"] = 0.0
        indexed_files = len(changed)
        skipped_files = len(unchanged)

    return {
        "discovered_files": discovered_files,
        "readable_files": readable_files,
        "readable_documents": readable_documents,
        "newly_indexed_files": len(new_files) if incremental else indexed_files,
        "modified_files": len(modified_files) if incremental else 0,
        "unchanged_files": skipped_files,
        "deleted_files": len(deleted_files),
        "chunks": sum(info["chunks"] for info in prepared.values()),
        "timings": {
            **timings,
            "total": _now() - started,
        },
        "full_rebuild": not incremental,
    }
