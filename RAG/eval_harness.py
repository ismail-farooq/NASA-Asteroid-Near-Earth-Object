"""
eval_harness.py
Automated quality checks for the asteroid RAG pipeline.

Evaluates:
  1. Faithfulness   — does the answer stay grounded in retrieved context?
  2. Relevance      — does the answer actually address the question?
  3. Retrieval hit  — do retrieved chunks contain expected keywords?

Usage:
    python RAG/eval_harness.py
    python RAG/eval_harness.py --output results.json
"""

import os
import json
import argparse
from dataclasses import dataclass, field, asdict
from pathlib import Path

from groq import Groq
from rag_pipeline import get_pipeline

# ── Test suite ─────────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "id": "TC01",
        "question": "What makes an asteroid potentially hazardous?",
        "expected_keywords": ["miss distance", "diameter", "close approach", "hazardous"],
    },
    {
        "id": "TC02",
        "question": "What is the Torino Scale?",
        "expected_keywords": ["torino", "impact", "probability", "scale"],
    },
    {
        "id": "TC03",
        "question": "How do astronomers measure an asteroid's orbit?",
        "expected_keywords": ["orbit", "semi-major axis", "eccentricity", "inclination"],
    },
    {
        "id": "TC04",
        "question": "What is the difference between an asteroid and a comet?",
        "expected_keywords": ["comet", "asteroid", "ice", "belt"],
    },
    {
        "id": "TC05",
        "question": "What was the Chicxulub impact event?",
        "expected_keywords": ["chicxulub", "extinction", "dinosaur", "impact"],
    },
    {
        "id": "TC06",
        "question": "How does NASA's planetary defense program work?",
        "expected_keywords": ["planetary defense", "nasa", "dart", "deflect"],
    },
    {
        "id": "TC07",
        "question": "What is an Apollo asteroid?",
        "expected_keywords": ["apollo", "earth-crossing", "orbit"],
    },
    {
        "id": "TC08",
        "question": "How is asteroid size estimated from brightness?",
        "expected_keywords": ["albedo", "magnitude", "diameter", "brightness"],
    },
    {
        "id": "TC09",
        "question": "What is a close approach and how is miss distance measured?",
        "expected_keywords": ["miss distance", "lunar distance", "kilometers", "close approach"],
    },
    {
        "id": "TC10",
        "question": "Which asteroid families are considered most dangerous to Earth?",
        "expected_keywords": ["aten", "apollo", "amor", "potentially hazardous"],
    },
]

# ── LLM judge prompt ───────────────────────────────────────────────────────────
JUDGE_PROMPT = """You are an impartial evaluator of RAG system outputs.

Question: {question}

Retrieved context (what the system had access to):
{context}

System answer:
{answer}

Score the answer on two dimensions, each from 0 to 10:
1. Faithfulness (0-10): Is every claim in the answer supported by the retrieved context?
   10 = fully grounded, 0 = completely hallucinated.
2. Relevance (0-10): Does the answer directly and completely address the question?
   10 = perfect answer, 0 = completely off-topic.

Respond ONLY with valid JSON in this exact format:
{{"faithfulness": <int>, "relevance": <int>, "reasoning": "<one sentence>"}}"""


@dataclass
class EvalResult:
    id:              str
    question:        str
    answer:          str
    faithfulness:    int    = 0
    relevance:       int    = 0
    retrieval_hit:   bool   = False
    reasoning:       str    = ""
    sources_count:   int    = 0
    error:           str    = ""


def keyword_hit(chunks: list[dict], keywords: list[str]) -> bool:
    """True if at least half the expected keywords appear in retrieved chunks."""
    combined = " ".join(c["preview"].lower() for c in chunks)
    hits = sum(1 for kw in keywords if kw.lower() in combined)
    return hits >= max(1, len(keywords) // 2)


def judge_answer(client: Groq, question: str, context: str, answer: str) -> dict:
    prompt = JUDGE_PROMPT.format(
        question=question, context=context[:3000], answer=answer
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"faithfulness": -1, "relevance": -1, "reasoning": f"Parse error: {raw}"}


def run_eval(output_path: str | None = None):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not set.")

    client   = Groq(api_key=api_key)
    pipeline = get_pipeline()

    results: list[EvalResult] = []

    print(f"{'='*60}")
    print(f"  Asteroid RAG Evaluation — {len(TEST_CASES)} test cases")
    print(f"{'='*60}\n")

    for tc in TEST_CASES:
        res = EvalResult(id=tc["id"], question=tc["question"], answer="")
        try:
            rag_out = pipeline.ask(tc["question"])
            res.answer       = rag_out["answer"]
            res.sources_count = len(rag_out["sources"])

            # Retrieval hit check
            res.retrieval_hit = keyword_hit(rag_out["sources"], tc["expected_keywords"])

            # LLM judge
            context_text = "\n\n".join(
                s["preview"] for s in rag_out["sources"]
            )
            scores = judge_answer(client, tc["question"], context_text, res.answer)
            res.faithfulness = scores.get("faithfulness", -1)
            res.relevance    = scores.get("relevance", -1)
            res.reasoning    = scores.get("reasoning", "")

        except Exception as e:
            res.error = str(e)

        results.append(res)

        status = "✓" if res.retrieval_hit else "✗"
        print(
            f"[{res.id}] {status} Retrieval | "
            f"Faithfulness: {res.faithfulness:>2}/10 | "
            f"Relevance: {res.relevance:>2}/10"
        )
        print(f"       Q: {res.question}")
        if res.error:
            print(f"       ERROR: {res.error}")
        else:
            print(f"       Judge: {res.reasoning}")
        print()

    # ── Summary ────────────────────────────────────────────────────────────────
    valid = [r for r in results if not r.error]
    avg_faith = sum(r.faithfulness for r in valid) / len(valid) if valid else 0
    avg_rel   = sum(r.relevance    for r in valid) / len(valid) if valid else 0
    hit_rate  = sum(1 for r in valid if r.retrieval_hit) / len(valid) if valid else 0

    print(f"{'='*60}")
    print(f"  SUMMARY")
    print(f"  Cases evaluated : {len(valid)} / {len(TEST_CASES)}")
    print(f"  Avg Faithfulness: {avg_faith:.1f} / 10")
    print(f"  Avg Relevance   : {avg_rel:.1f}   / 10")
    print(f"  Retrieval Hit % : {hit_rate*100:.0f}%")
    print(f"{'='*60}")

    if output_path:
        payload = {
            "summary": {
                "cases": len(TEST_CASES),
                "valid": len(valid),
                "avg_faithfulness": round(avg_faith, 2),
                "avg_relevance": round(avg_rel, 2),
                "retrieval_hit_rate": round(hit_rate, 4),
            },
            "results": [asdict(r) for r in results],
        }
        Path(output_path).write_text(json.dumps(payload, indent=2))
        print(f"\n[eval] Results saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None, help="Optional path to save JSON results")
    args = parser.parse_args()
    run_eval(output_path=args.output)