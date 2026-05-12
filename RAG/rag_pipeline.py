"""
rag_pipeline.py
LangChain RAG chain over the asteroid wiki corpus.

Exposes:
  ask(question, asteroid_context=None) -> dict
    { "answer": str, "sources": list[dict], "model": str }

The optional `asteroid_context` dict is injected when the Flask app
wants the RAG answer to be grounded in the current session's asteroid data
(e.g. after a hazard prediction).
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from retriever import AsteroidRetriever

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ── Config ─────────────────────────────────────────────────────────────────────
LLM_MODEL = "llama-3.3-70b-versatile"   # free on Groq, very capable
TOP_K     = 5

# ── System / RAG prompt ────────────────────────────────────────────────────────
SYSTEM_TEMPLATE = """You are ASTEROID-GPT, an expert on Near-Earth Objects (NEOs),
asteroid science, and planetary defense. You answer questions using the retrieved
context below. If the context does not contain enough information, say so honestly
rather than speculating.

When an asteroid's orbital/physical data is provided, incorporate it naturally
into your answer to give a personalised explanation.

Retrieved context:
{context}

{asteroid_section}"""

HUMAN_TEMPLATE = "{question}"


def _format_asteroid_section(asteroid: dict | None) -> str:
    if not asteroid:
        return ""
    lines = [f"  {k}: {v}" for k, v in asteroid.items()]
    return "Current asteroid data:\n" + "\n".join(lines)


class RAGPipeline:
    def __init__(self, api_key: str | None = None):
        api_key = os.getenv("GROQ_API_KEY") 
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY not set.")

        self.retriever = AsteroidRetriever()
        self.llm       = ChatGroq(model=LLM_MODEL, temperature=0.3, groq_api_key=api_key)
        self.parser    = StrOutputParser()

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_TEMPLATE),
            ("human",  HUMAN_TEMPLATE),
        ])

    # ── Public API ──────────────────────────────────────────────────────────────

    def ask(self, question: str, asteroid_context: dict | None = None) -> dict:
        """
        Args:
            question         : user's natural-language question
            asteroid_context : optional dict from Flask session['current_asteroid']

        Returns:
            {
              "answer":  str,
              "sources": [{"chunk_index": int, "distance": float, "preview": str}],
              "model":   str
            }
        """
        # 1. Retrieve relevant chunks
        chunks  = self.retriever.retrieve(question, top_k=TOP_K)
        context = "\n\n---\n\n".join(c["text"] for c in chunks)

        # 2. Build asteroid section
        asteroid_section = _format_asteroid_section(asteroid_context)

        # 3. Build and invoke chain
        chain = self.prompt | self.llm | self.parser
        answer = chain.invoke({
            "context":         context,
            "asteroid_section": asteroid_section,
            "question":        question,
        })

        # 4. Package sources (trim to 200-char preview so JSON stays lean)
        sources = [
            {
                "chunk_index": c["chunk_index"],
                "distance":    c["distance"],
                "preview":     c["text"][:200],
            }
            for c in chunks
        ]

        return {"answer": answer, "sources": sources, "model": LLM_MODEL}


# ── Singleton for Flask import ─────────────────────────────────────────────────
_pipeline: RAGPipeline | None = None

def get_pipeline() -> RAGPipeline:
    """Return a module-level singleton so the LLM client isn't recreated per request."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


# ── CLI smoke-test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = get_pipeline()
    result = p.ask("What is the Torino Scale and how is it used?")
    print("Answer:\n", result["answer"])
    print("\nSources retrieved:", len(result["sources"]))
    for s in result["sources"]:
        print(f"  chunk {s['chunk_index']} (dist={s['distance']}): {s['preview'][:80]}…")