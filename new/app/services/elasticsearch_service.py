from datetime import datetime

from elasticsearch import Elasticsearch

from app.config import (
    ES_HOST,
    ES_USER,
    ES_PASS,
    ES_CERT_PATH,
    CHAT_SESSION_INDEX,
    CHAT_MESSAGE_INDEX,
    CHAT_MEMORY_INDEX
)

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    ca_certs=ES_CERT_PATH
)
print("ELASTICSEARCH_SERVICE_LOADED")


def semantic_search(
    index,
    query_vector,
    top_k,
    attachment_ids=None
):

    print("SEMANTIC_SEARCH_CALLED")
    print("attachment_ids =", attachment_ids)

    if attachment_ids is None:
        attachment_ids = []

    knn_query = {
        "field": "embedding",
        "query_vector": query_vector,
        "k": top_k,
        "num_candidates": 100
    }

    if attachment_ids:
        knn_query["filter"] = {
            "terms": {
                "attachment_id": attachment_ids
            }
        }

    return es.search(
        index=index,
        knn=knn_query
    )

def keyword_search(
    index,
    query,
    attachment_ids=None
):

    if attachment_ids is None:
        attachment_ids = []

    search_query = {
        "match": {
            "combined": {
                "query": query,
                "operator": "or",
                "fuzziness": "AUTO"
            }
        }
    }

    if attachment_ids:
        search_query = {
            "bool": {
                "must": [
                    {
                        "match": {
                            "combined": {
                                "query": query,
                                "operator": "or",
                                "fuzziness": "AUTO"
                            }
                        }
                    }
                ],
                "filter": [
                    {
                        "terms": {
                            "attachment_id": attachment_ids
                        }
                    }
                ]
            }
        }

    return es.search(
        index=index,
        query=search_query,
        size=100
    )


def create_session(
    session_id,
    title="New Chat"
):

    doc = {
        "session_id": session_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    return es.index(
        index=CHAT_SESSION_INDEX,
        document=doc
    )


def save_chat_message(
    session_id,
    role,
    content
):

    doc = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }

    return es.index(
        index=CHAT_MESSAGE_INDEX,
        document=doc
    )


def get_recent_messages(
    session_id,
    limit=10
):

    response = es.search(
        index=CHAT_MESSAGE_INDEX,
        query={
            "term": {
                "session_id": session_id
            }
        },
        sort=[
            {
                "created_at": {
                    "order": "desc"
                }
            }
        ],
        size=limit
    )

    return [
        hit["_source"]
        for hit in reversed(
            response["hits"]["hits"]
        )
    ]


def count_messages(
    session_id
):

    response = es.count(
        index=CHAT_MESSAGE_INDEX,
        query={
            "term": {
                "session_id": session_id
            }
        }
    )

    return response["count"]


def store_memory_chunk(
    session_id,
    chunk_text,
    embedding
):

    doc = {
        "session_id": session_id,
        "chunk_text": chunk_text,
        "embedding": embedding,
        "created_at": datetime.utcnow().isoformat()
    }

    return es.index(
        index=CHAT_MEMORY_INDEX,
        document=doc
    )


def retrieve_memory_chunks(
    session_id,
    query_embedding,
    top_k=5
):

    return es.search(
        index=CHAT_MEMORY_INDEX,
        knn={
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": 50
        },
        query={
            "term": {
                "session_id": session_id
            }
        }
    )