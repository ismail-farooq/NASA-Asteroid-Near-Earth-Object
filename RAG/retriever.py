"""
retriever.py
Query interface over the ChromaDB asteroid knowledge store.
Used by rag_pipeline.py and directly by the Flask route.
"""

import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

# ── Paths / Config ─────────────────────────────────────────────────────────────
CHROMA_DIR  = Path(__file__).parent / "chroma_store"
COLLECTION  = "asteroid_knowledge"
EMBED_MODEL = "all-MiniLM-L6-v2"   # must match ingest.py
TOP_K       = 5


class AsteroidRetriever:
    def __init__(self, api_key: str | None = None):
        # api_key param kept for interface compatibility but not needed
        self.model = SentenceTransformer(EMBED_MODEL)

        if not CHROMA_DIR.exists():
            raise FileNotFoundError(
                f"ChromaDB store not found at {CHROMA_DIR}. "
                "Run `python RAG/ingest.py` first."
            )

        chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = chroma.get_collection(COLLECTION)

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        embedding = self._embed(query)
        results   = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({
                "text":        doc,
                "chunk_index": meta.get("chunk_index"),
                "distance":    round(dist, 4),
            })
        return chunks

    def retrieve_as_context(self, query: str, top_k: int = TOP_K) -> str:
        chunks = self.retrieve(query, top_k)
        return "\n\n---\n\n".join(
            f"[Chunk {c['chunk_index']}] {c['text']}" for c in chunks
        )

    def _embed(self, text: str) -> list[float]:
        return self.model.encode([text]).tolist()[0]


# ── Quick smoke-test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    r = AsteroidRetriever()
    query = "What makes an asteroid potentially hazardous?"
    chunks = r.retrieve(query)
    print(f"Query: {query}\n")
    for i, c in enumerate(chunks, 1):
        print(f"[{i}] (dist={c['distance']}) {c['text'][:200]}\n")