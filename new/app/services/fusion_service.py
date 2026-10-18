from collections import defaultdict


def rrf_fusion(vector_hits, keyword_hits, k=60):

    scores = defaultdict(float)
    doc_map = {}

    rankings = [
        [hit["_id"] for hit in keyword_hits],
        [hit["_id"] for hit in vector_hits]
    ]

    for hit in keyword_hits + vector_hits:
        doc_map[hit["_id"]] = hit["_source"]

    for ranking in rankings:

        for rank, doc_id in enumerate(ranking):

            scores[doc_id] += (
                1 / (k + rank + 1)
            )

    return sorted(
        [
            {
                "score": score,
                "source": doc_map[doc_id]
            }
            for doc_id, score in scores.items()
        ],
        key=lambda x: x["score"],
        reverse=True
    )


def build_memory_context(
    recent_messages,
    memories
):

    context_parts = []

    context_parts.append(
        "RECENT CONVERSATION\n"
    )

    for msg in recent_messages:

        context_parts.append(
            f"{msg['role']}: {msg['content']}"
        )

    context_parts.append(
        "\nLONG TERM MEMORY\n"
    )

    for memory in memories:

        context_parts.append(memory)

    return "\n".join(context_parts)