import functools
import logging
import os
import shutil
import threading
from typing import Optional

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Import config variables
try:
    from config import DATA_PATH, CHROMA_PATH, EMBEDDING_MODEL_NAME
except ImportError:
    from .config import DATA_PATH, CHROMA_PATH, EMBEDDING_MODEL_NAME

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_chroma_cache_lock = threading.Lock()
_cached_chroma_instance: Optional[Chroma] = None


def load_documents(data_path=DATA_PATH):
    """Loads documents from the specified directory using different loaders."""
    logging.info(f"Loading documents from {data_path}...")
    loader_configs = [
        {"glob": "**/*.pdf", "loader_cls": PyPDFLoader, "loader_kwargs": {}},
        {"glob": "**/*.txt", "loader_cls": TextLoader, "loader_kwargs": {"encoding": "utf-8"}},
    ]
    documents = []
    for config in loader_configs:
        try:
            loader = DirectoryLoader(
                data_path,
                glob=config["glob"],
                loader_cls=config["loader_cls"],
                loader_kwargs=config.get("loader_kwargs", {}),
                show_progress=True,
                use_multithreading=True
            )
            loaded_docs = loader.load()
            if loaded_docs:
                logging.info(f"Loaded {len(loaded_docs)} documents using {config['loader_cls'].__name__}")
                documents.extend(loaded_docs)
            else:
                logging.info(f"No documents found for glob pattern {config['glob']}")
        except Exception as e:
            logging.error(f"Error loading files with {config['loader_cls'].__name__}: {e}", exc_info=True)

    if not documents:
        logging.warning("No documents were loaded. Ensure files exist in the data directory and loaders are configured correctly.")
    else:
        logging.info(f"Total documents loaded: {len(documents)}")
    return documents


def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """Splits documents into manageable chunks."""
    logging.info(f"Splitting {len(documents)} documents into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    logging.info(f"Split into {len(chunks)} chunks.")
    return chunks


@functools.lru_cache(maxsize=1)
def get_embedding_function():
    """Initializes and returns the singleton embedding function."""
    logging.info(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )
    return embeddings


def clear_cached_chroma():
    """Invalidate the cached ChromaDB instance (e.g. after rebuild or delete)."""
    global _cached_chroma_instance
    with _chroma_cache_lock:
        _cached_chroma_instance = None


def get_cached_chroma():
    """Initializes and returns the Chroma vectorstore, cached to avoid recreation per query."""
    global _cached_chroma_instance
    with _chroma_cache_lock:
        if _cached_chroma_instance is not None:
            return _cached_chroma_instance

        if not os.path.exists(CHROMA_PATH) or not os.path.isdir(CHROMA_PATH):
            return None

        logging.info(f"Loading ChromaDB from {CHROMA_PATH} for cache...")
        embedding_function = get_embedding_function()
        try:
            _cached_chroma_instance = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
            logging.info("Successfully loaded and cached ChromaDB.")
            return _cached_chroma_instance
        except Exception as e:
            logging.error(f"Failed to load existing ChromaDB for cache: {e}", exc_info=True)
            return None


def setup_vectorstore(documents, chroma_path=CHROMA_PATH, embedding_function=None):
    """Creates and persists the ChromaDB vector store."""
    if not documents:
        logging.warning("No documents provided to setup_vectorstore. Skipping DB creation.")
        return None

    if embedding_function is None:
        embedding_function = get_embedding_function()

    if os.path.exists(chroma_path):
        logging.info(f"Existing ChromaDB found at {chroma_path}.")
        try:
            return Chroma(persist_directory=chroma_path, embedding_function=embedding_function)
        except Exception as e:
            logging.error(f"Failed to load existing ChromaDB: {e}", exc_info=True)

    logging.info(f"Creating new ChromaDB vector store at {chroma_path}...")
    chunks = split_documents(documents)
    if not chunks:
        logging.error("No chunks generated from documents. Cannot create vector store.")
        return None

    try:
        clear_cached_chroma()
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_function,
            persist_directory=chroma_path
        )
        logging.info(f"Vector store created successfully and persisted at {chroma_path}.")
        return vectorstore
    except Exception as e:
        logging.error(f"Failed to create ChromaDB vector store: {e}", exc_info=True)
        return None


def get_vectorstore_retriever(k=4, chroma_path=CHROMA_PATH, embedding_function=None):
    """Loads the vector store and returns a retriever."""
    if not os.path.exists(chroma_path):
        logging.error(f"ChromaDB path '{chroma_path}' does not exist. Run setup_vectorstore or rebuild first.")
        raise FileNotFoundError(f"ChromaDB not found at {chroma_path}")

    try:
        if chroma_path == CHROMA_PATH:
            vectorstore = get_cached_chroma()
            if vectorstore is None:
                raise RuntimeError("Failed to get cached Chroma client.")
        else:
            if embedding_function is None:
                embedding_function = get_embedding_function()
            vectorstore = Chroma(persist_directory=chroma_path, embedding_function=embedding_function)

        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': k, 'lambda_mult': 0.25}
        )
        logging.info(f"ChromaDB retriever loaded successfully with k={k}.")
        return retriever
    except Exception as e:
        logging.error(f"Failed to load ChromaDB or create retriever: {e}", exc_info=True)
        raise
