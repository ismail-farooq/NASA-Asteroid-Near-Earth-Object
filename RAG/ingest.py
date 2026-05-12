"""
ingest.py
Chunks the asteroid wiki corpus, embeds via OpenAI, and stores in ChromaDB.
Run once (or re-run to refresh the vector store).

Usage:
    python RAG/ingest.py
"""

import os
import re
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent
WIKI_PATH  = BASE_DIR / "Datasets" / "NLP" / "asteroids_wiki_cleaned.txt"
CHROMA_DIR = Path(__file__).parent / "chroma_store"

# ── Config ─────────────────────────────────────────────────────────────────────
EMBED_MODEL  = "all-MiniLM-L6-v2"   # free, local, fast (~80MB download once)
COLLECTION   = "asteroid_knowledge"
CHUNK_SIZE   = 500    # characters per chunk
CHUNK_OVERLAP = 80    # overlap between consecutive chunks


def load_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Sliding-window character chunker.
    Splits on sentence boundaries where possible to avoid mid-sentence cuts.
    """
    # Normalise whitespace
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))

        # Try to end on a sentence boundary ('. ', '? ', '! ')
        if end < len(text):
            boundary = max(
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end),
            )
            if boundary != -1:
                end = boundary + 1   # include the period

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end - overlap > start else end

    return chunks


def embed_chunks(model: SentenceTransformer, chunks: list[str]) -> list[list[float]]:
    """Batch-embed all chunks locally using sentence-transformers."""
    embeddings = model.encode(chunks, show_progress_bar=True)
    return embeddings.tolist()


def build_store():
    print(f"[ingest] Loading corpus from {WIKI_PATH} …")
    text   = load_text(WIKI_PATH)
    chunks = chunk_text(text)
    print(f"[ingest] {len(chunks)} chunks created.")

    print(f"[ingest] Loading local embedding model '{EMBED_MODEL}' …")
    embed_model = SentenceTransformer(EMBED_MODEL)

    print("[ingest] Embedding chunks locally …")
    embeddings = embed_chunks(embed_model, chunks)

    print(f"[ingest] Storing in ChromaDB at {CHROMA_DIR} …")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Drop and recreate so re-runs are idempotent
    try:
        chroma.delete_collection(COLLECTION)
    except Exception:
        pass

    col = chroma.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    ids        = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas  = [{"source": "asteroids_wiki", "chunk_index": i} for i in range(len(chunks))]

    col.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    print(f"[ingest] ✓ {col.count()} chunks stored in collection '{COLLECTION}'.")


if __name__ == "__main__":
    build_store()