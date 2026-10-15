import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.documents import Document

from src import vectorstore_indexer as indexer


class _Embeddings:
    def embed_documents(self, texts):
        return [[float(len(text))] for text in texts]


class _Store:
    def __init__(self, path, embedding_function=None):
        self.path = Path(path)
        self.state_path = self.path / "items.json"
        self.items = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}

    def _save(self):
        self.state_path.write_text(json.dumps(self.items))

    def add_documents(self, documents, ids):
        for document, item_id in zip(documents, ids):
            self.items[item_id] = document.page_content
        self._save()

    def delete(self, ids):
        for item_id in ids:
            self.items.pop(item_id, None)
        self._save()


class _System:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class _Client:
    def __init__(self):
        self._system = _System()


class TestVectorStoreIndexer(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.data = Path(self.workspace.name) / "data"
        self.store = Path(self.workspace.name) / "chroma"
        self.data.mkdir()
        self.load_calls = []

        def load_file(path, source, fingerprint):
            self.load_calls.append(source)
            return [Document(page_content=Path(path).read_text(), metadata={})]

        self.load_file = load_file
        self.patches = [
            patch.object(indexer, "_open_store", side_effect=lambda path, embedding: _Store(path, embedding)),
            patch.object(indexer, "get_embedding_function", return_value=_Embeddings()),
            patch.object(indexer, "_load_file", side_effect=self.load_file),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.workspace.cleanup()

    def _index(self, full=False):
        return indexer.index_documents(str(self.data), str(self.store), full=full)

    def test_first_index_and_unchanged_repeat(self):
        (self.data / "one.txt").write_text("one " * 400)
        first = self._index()
        self.assertTrue(first["full_rebuild"])
        self.assertEqual(first["newly_indexed_files"], 1)
        self.assertEqual(self.load_calls, ["one.txt"])
        manifest = json.loads((self.store / indexer.MANIFEST_FILENAME).read_text())
        file_metadata = manifest["files"]["one.txt"]
        self.assertEqual(manifest["metadata"]["file_count"], 1)
        self.assertEqual(manifest["metadata"]["document_count"], 1)
        self.assertEqual(manifest["metadata"]["chunk_count"], file_metadata["chunks"])
        self.assertEqual(file_metadata["chunks"], len(file_metadata["ids"]))
        self.assertEqual(manifest["embedding_model"], indexer.EMBEDDING_MODEL_NAME)
        self.assertEqual(manifest["index_config"], indexer.INDEX_CONFIG)

        self.load_calls.clear()
        repeat = self._index()
        self.assertFalse(repeat["full_rebuild"])
        self.assertEqual(repeat["unchanged_files"], 1)
        self.assertEqual(repeat["chunks"], first["chunks"])
        self.assertEqual(self.load_calls, [])

    def test_add_modify_delete(self):
        (self.data / "one.txt").write_text("one " * 400)
        self._index()
        (self.data / "two.txt").write_text("two " * 400)
        (self.data / "one.txt").write_text("changed " * 400)
        result = self._index()
        self.assertEqual(result["newly_indexed_files"], 1)
        self.assertEqual(result["modified_files"], 1)
        self.assertEqual(result["deleted_files"], 0)

        (self.data / "two.txt").unlink()
        result = self._index()
        self.assertEqual(result["deleted_files"], 1)
        manifest = json.loads((self.store / indexer.MANIFEST_FILENAME).read_text())
        self.assertEqual(set(manifest["files"]), {"one.txt"})

    def test_embedding_model_change_forces_full_rebuild(self):
        (self.data / "one.txt").write_text("one " * 400)
        self._index()
        with patch.object(indexer, "EMBEDDING_MODEL_NAME", "different-model"):
            result = self._index()
        self.assertTrue(result["full_rebuild"])

    def test_index_config_change_forces_full_rebuild(self):
        (self.data / "one.txt").write_text("one " * 400)
        self._index()
        with patch.object(
            indexer,
            "INDEX_CONFIG",
            {**indexer.INDEX_CONFIG, "chunk_overlap": 100},
        ):
            result = self._index()
        self.assertTrue(result["full_rebuild"])

    def test_incremental_failure_keeps_live_store_and_manifest(self):
        (self.data / "one.txt").write_text("one " * 400)
        self._index()
        before_manifest = (self.store / indexer.MANIFEST_FILENAME).read_text()
        before_items = (self.store / "items.json").read_text()
        (self.data / "one.txt").write_text("changed " * 400)
        with patch.object(indexer, "_add_batches", side_effect=RuntimeError("write failed")):
            with self.assertRaises(RuntimeError):
                self._index()
        self.assertEqual((self.store / indexer.MANIFEST_FILENAME).read_text(), before_manifest)
        self.assertEqual((self.store / "items.json").read_text(), before_items)

    def test_full_rebuild_releases_cached_client_before_replacement(self):
        (self.data / "one.txt").write_text("one " * 400)
        with patch.object(indexer, "clear_cached_chroma") as clear_cached:
            self._index(full=True)
        clear_cached.assert_called_once()

    def test_close_store_stops_chroma_system_before_publication(self):
        store = _Store(self.store, _Embeddings())
        store._client = _Client()

        indexer._close_store(store)

        self.assertTrue(store._client._system.stopped)

    def test_successful_directory_replacement_removes_old_store(self):
        source = Path(self.workspace.name) / "staging"
        source.mkdir()
        (source / "marker.txt").write_text("new")
        (self.store / "marker.txt").parent.mkdir()
        (self.store / "marker.txt").write_text("old")

        indexer._safe_replace_directory(str(source), str(self.store))

        self.assertEqual((self.store / "marker.txt").read_text(), "new")
        self.assertFalse(source.exists())
        self.assertFalse(any(
            path.name.startswith("chroma.backup-")
            for path in Path(self.workspace.name).iterdir()
        ))

    def test_failed_directory_replacement_preserves_existing_store(self):
        source = Path(self.workspace.name) / "staging"
        source.mkdir()
        (source / "marker.txt").write_text("new")
        self.store.mkdir()
        (self.store / "marker.txt").write_text("old")
        real_replace = indexer.os.replace

        def fail_publishing_source(from_path, to_path):
            if os.path.abspath(from_path) == os.path.abspath(source):
                raise PermissionError(5, "Access is denied", from_path)
            return real_replace(from_path, to_path)

        with patch.object(indexer.os, "replace", side_effect=fail_publishing_source):
            with self.assertRaisesRegex(RuntimeError, "existing store was preserved"):
                indexer._safe_replace_directory(str(source), str(self.store))

        self.assertEqual((self.store / "marker.txt").read_text(), "old")
        self.assertTrue(source.exists())
        self.assertFalse(any(
            path.name.startswith("chroma.backup-")
            for path in Path(self.workspace.name).iterdir()
        ))

    def test_full_rebuild_failure_cleans_staging_and_preserves_store(self):
        (self.data / "one.txt").write_text("one " * 400)
        self._index()
        before_items = (self.store / "items.json").read_text()
        (self.data / "one.txt").write_text("changed " * 400)

        with patch.object(
            indexer,
            "_safe_replace_directory",
            side_effect=RuntimeError("publish failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "publish failed"):
                self._index(full=True)

        self.assertEqual((self.store / "items.json").read_text(), before_items)
        self.assertFalse(any(
            path.name.startswith(".chroma.staging-")
            for path in Path(self.workspace.name).iterdir()
        ))


if __name__ == "__main__":
    unittest.main()
