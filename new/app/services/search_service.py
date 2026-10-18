from app.services.embedding_service import get_embedding
from app.services.elasticsearch_service import (
    semantic_search,
    keyword_search
)

from app.utils.query_utils import extract_entity
from app.config import INDEX_NAME


def run_search(
    query,
    top_k,
    logger,
    attachment_ids=None
):
    logger.info(
        f"Running search for query: {query}"
    )

    if attachment_ids is None:
        attachment_ids = []

    logger.info(
        f"Attachment IDs received: {attachment_ids}"
    )

    query_vector = get_embedding(query)

    vector_response = semantic_search(
        INDEX_NAME,
        query_vector,
        top_k,
        attachment_ids=attachment_ids
    )

    vector_hits = vector_response["hits"]["hits"]

    keyword_hits = []

    if extract_entity(query):

        logger.info(
            "Keyword search enabled"
        )

        keyword_response = keyword_search(
            INDEX_NAME,
            query,
            attachment_ids=attachment_ids
        )

        keyword_hits = keyword_response["hits"]["hits"]

    else:

        logger.info(
            "Keyword search skipped"
        )

    logger.info(
        f"Vector Results: {len(vector_hits)}"
    )

    logger.info(
        f"Keyword Results: {len(keyword_hits)}"
    )

    return vector_hits, keyword_hits