"""
RAG ROUTES — paste these into App/app.py
─────────────────────────────────────────
Add to top-level imports:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "RAG"))
    from rag_pipeline import get_pipeline

Then add the two routes below.
"""

import sys
from pathlib import Path

# ── Add RAG folder to path (put this near the top of app.py) ──────────────────
sys.path.insert(0, str(Path(__file__).parent.parent / "RAG"))

from rag_pipeline import get_pipeline   # lazy-loaded singleton


# ── Route: RAG chat page ───────────────────────────────────────────────────────
@app.route("/chat")
def chat():
    """Renders the RAG chat UI."""
    return render_template("chat.html")


# ── Route: RAG API endpoint (called by chat.html via fetch) ───────────────────
@app.route("/api/rag", methods=["POST"])
def rag_query():
    """
    POST JSON: { "question": str }
    Optionally injects the current session asteroid as context.

    Returns JSON:
    {
      "answer":  str,
      "sources": [{ "chunk_index": int, "distance": float, "preview": str }],
      "model":   str
    }
    """
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "No question provided."}), 400

    # Pull current asteroid from session if one exists
    asteroid_context = session.get("current_asteroid")

    try:
        pipeline = get_pipeline()
        result   = pipeline.ask(question, asteroid_context=asteroid_context)
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"RAG error: {e}"}), 500