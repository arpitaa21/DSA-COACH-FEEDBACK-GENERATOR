"""
rag/evaluation.py
------------------
Lightweight, dependency-free evaluation of retrieval quality - inspired by
RAGAS-style metrics (hit rate / context precision, reciprocal rank) without
pulling in the full `ragas` package, which brings a heavy dependency tree
that's overkill for a knowledge base this size.

Since this build has no separate retriever.py, evaluation exercises
VectorIndex.search() directly with embedded queries - that search call *is*
the retrieval step being evaluated.

Run it directly:

    cd backend
    python -m rag.evaluation

(Assumes ingestion has already been run at least once - it loads the saved
index rather than rebuilding it.)
"""
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

from .embeddings import embed_query
from .indexing import VectorIndex

# A small, hand-labeled gold set: for each query, which document(s) SHOULD
# show up in the retrieved chunks. Keyed by doc_id (matches the knowledge
# base filenames in rag/data/knowledge_base/), so this stays correct even if
# chunk boundaries shift.
GOLD_QUERIES = [
    {"query": "how do I solve problems with a fixed-size window efficiently", "expected_doc_id": "sliding-window"},
    {"query": "finding a pair in a sorted array that sums to a target", "expected_doc_id": "two-pointers"},
    {"query": "searching a sorted array in logarithmic time", "expected_doc_id": "binary-search"},
    {"query": "overlapping subproblems and memoization", "expected_doc_id": "dynamic-programming"},
    {"query": "shortest path in an unweighted graph", "expected_doc_id": "graph-traversal"},
    {"query": "generating all valid combinations with pruning", "expected_doc_id": "backtracking"},
]


@dataclass
class QueryResult:
    query: str
    expected_doc_id: str
    retrieved_doc_ids: list[str]
    hit: bool
    reciprocal_rank: float
    top_score: float


def evaluate_retrieval(top_k: int = 3, index: VectorIndex | None = None) -> dict:
    """Runs every gold query against the index and reports hit-rate@k, mean
    reciprocal rank, and average top-1 similarity score."""
    index = index or VectorIndex.load()

    results: list[QueryResult] = []
    for item in GOLD_QUERIES:
        query_vector = embed_query(item["query"])
        hits = index.search(query_vector, top_k=top_k)

        retrieved_doc_ids = [h["chunk"].doc_id for h in hits]
        rank = next(
            (i + 1 for i, doc_id in enumerate(retrieved_doc_ids) if doc_id == item["expected_doc_id"]),
            None,
        )

        results.append(
            QueryResult(
                query=item["query"],
                expected_doc_id=item["expected_doc_id"],
                retrieved_doc_ids=retrieved_doc_ids,
                hit=rank is not None,
                reciprocal_rank=(1.0 / rank) if rank else 0.0,
                top_score=hits[0]["score"] if hits else 0.0,
            )
        )

    n = len(results)
    hit_rate = sum(r.hit for r in results) / n if n else 0.0
    mean_reciprocal_rank = sum(r.reciprocal_rank for r in results) / n if n else 0.0
    avg_top_score = sum(r.top_score for r in results) / n if n else 0.0

    return {
        "top_k": top_k,
        "num_queries": n,
        "hit_rate_at_k": round(hit_rate, 3),
        "mean_reciprocal_rank": round(mean_reciprocal_rank, 3),
        "avg_top1_similarity": round(avg_top_score, 3),
        "per_query": [
            {
                "query": r.query,
                "expected_doc_id": r.expected_doc_id,
                "retrieved_doc_ids": r.retrieved_doc_ids,
                "hit": r.hit,
            }
            for r in results
        ],
    }


if __name__ == "__main__":
    report = evaluate_retrieval()
    print(f"Retrieval evaluation (top_k={report['top_k']}, {report['num_queries']} queries):")
    print(f"  hit_rate@k:            {report['hit_rate_at_k']}")
    print(f"  mean reciprocal rank:  {report['mean_reciprocal_rank']}")
    print(f"  avg top-1 similarity:  {report['avg_top1_similarity']}")
    print()
    for row in report["per_query"]:
        mark = "PASS" if row["hit"] else "FAIL"
        print(f"  [{mark}] \"{row['query']}\" -> expected {row['expected_doc_id']}, got {row['retrieved_doc_ids']}")
