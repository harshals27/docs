from app.services.embedding_service import get_embedding

from app.services.elasticsearch_service import (
    store_memory_chunk,
    retrieve_memory_chunks
)


def create_memory_chunk(
    session_id,
    messages
):

    chunk_text = "\n".join(
        [
            f"{m['role']}: {m['content']}"
            for m in messages
        ]
    )

    embedding = get_embedding(
        chunk_text
    )

    store_memory_chunk(
        session_id,
        chunk_text,
        embedding
    )


def get_relevant_memories(
    session_id,
    user_query,
    top_k=5
):

    try:

        query_embedding = get_embedding(
            user_query
        )

        response = retrieve_memory_chunks(
            session_id,
            query_embedding,
            top_k
        )

        return [
            hit["_source"]["chunk_text"]
            for hit in response["hits"]["hits"]
        ]

    except Exception:
        return []