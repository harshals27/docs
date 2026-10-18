from fastapi import APIRouter

from app.models.request_models import ChatRequest
from app.logger import get_logger

from app.services.search_service import run_search

from app.services.fusion_service import (
    rrf_fusion,
    build_memory_context
)

from app.services.llm_service import call_llm

from app.utils.query_utils import rewrite_query_with_context

from app.config import (
    LOW_CONFIDENCE_THRESHOLD,
    MAX_CONTEXT_DOCS,
    SYSTEM_PROMPT,
    MEMORY_CHUNK_SIZE,
    RECENT_MESSAGE_LIMIT
)

from app.services.chat_history_service import (
    store_user_message,
    store_assistant_message,
    fetch_recent_chat,
    get_message_count
)

from app.services.memory_service import (
    get_relevant_memories,
    create_memory_chunk
)

router = APIRouter()
logger = get_logger()


@router.post("/chat")
def chat(req: ChatRequest):

    try:

        if not req.messages:
            return {"error": "No messages provided"}

        session_id = req.session_id
        messages = req.messages

        attachment_ids = getattr(
            req,
            "attachment_ids",
            []
        )

        raw_query = next(
            (
                m["content"]
                for m in reversed(messages)
                if m["role"] == "user"
            ),
            ""
        )

        store_user_message(
            session_id,
            raw_query
        )

        logger.info(f"Raw Query: {raw_query}")

        user_query = rewrite_query_with_context(
            messages,
            logger
        )

        user_query_cleaned = (
            user_query
            .lower()
            .strip()
        )

        logger.info(
            f"Final Query: {user_query_cleaned}"
        )

        logger.info(
            f"Attachment IDs: {attachment_ids}"
        )

        vector_hits, keyword_hits = run_search(
            query=user_query_cleaned,
            top_k=req.top_k,
            logger=logger,
            attachment_ids=attachment_ids
        )

        logger.info("===== SEARCH RESULTS =====")

        logger.info(
            f"Vector Hits Returned: {len(vector_hits)}"
        )

        logger.info(
            f"Keyword Hits Returned: {len(keyword_hits)}"
        )

        for i, hit in enumerate(vector_hits[:3]):
            logger.info(
                f"[VECTOR] Rank {i+1} | "
                f"Score: {hit['_score']} | "
                f"ID: {hit['_id']}"
            )

        for i, hit in enumerate(keyword_hits[:3]):
            logger.info(
                f"[KEYWORD] Rank {i+1} | "
                f"Score: {hit['_score']} | "
                f"ID: {hit['_id']}"
            )

        sorted_hits = rrf_fusion(
            vector_hits,
            keyword_hits
        )

        logger.info("===== RRF RESULTS =====")

        logger.info(
            f"Total fused documents: {len(sorted_hits)}"
        )

        for i, hit in enumerate(sorted_hits[:5]):
            logger.info(
                f"[RRF] Rank {i+1} | "
                f"Score: {hit['score']}"
            )

        max_score = (
            sorted_hits[0]["score"]
            if sorted_hits
            else 0
        )

        logger.info(
            f"Hybrid Max Score: {max_score}"
        )

        if max_score < LOW_CONFIDENCE_THRESHOLD:
            return {
                "reply": "No relevant context found.",
                "sources": [],
                "llm_called": False
            }

        top_hits = sorted_hits[:MAX_CONTEXT_DOCS]

        # ==================================
        # Citation Extraction
        # ==================================

        sources = []
        seen_sources = set()

        for hit in top_hits:

            source_data = hit["source"]

            source_file = source_data.get(
                "source_file"
            )

            if not source_file:
                continue

            unique_key = (
                source_file,
                source_data.get("version")
            )

            if unique_key in seen_sources:
                continue

            seen_sources.add(unique_key)

            sources.append(
                {
                    "source_file": source_file,
                    "category": source_data.get(
                        "category"
                    ),
                    "version": source_data.get(
                        "version"
                    ),
                    "created_by": source_data.get(
                        "created_by"
                    ),
                    "created_date": source_data.get(
                        "created_date"
                    )
                }
            )

        logger.info(
            "===== SOURCES ====="
        )

        for source in sources:
            logger.info(source)

        # ==================================
        # Context Building
        # ==================================

        context_blocks = []

        for i, hit in enumerate(top_hits):

            text = (
                hit["source"]["combined"]
                .replace("<br>", "\n")
            )

            context_blocks.append(
                f"Document {i+1}:\n{text}"
            )

        retrieved_context = "\n\n".join(
            context_blocks
        )

        recent_messages = fetch_recent_chat(
            session_id,
            RECENT_MESSAGE_LIMIT
        )

        memories = get_relevant_memories(
            session_id,
            user_query
        )

        memory_context = build_memory_context(
            recent_messages,
            memories
        )

        logger.info(
            "===== CONTEXT SENT TO LLM ====="
        )

        logger.info(
            retrieved_context[:1500]
        )

        chat_history = [
            {
                "role": m["role"],
                "content": m["content"]
            }
            for m in messages[-4:-1]
        ]

        chat_history.append(
            {
                "role": "user",
                "content": user_query
            }
        )

        payload = {
            "project_name": "NAVRTA-RAG",
            "stream": False,
            "response_format": {
                "type": "json_object"
            },
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "system",
                    "content": f"""
SESSION MEMORY

{memory_context}

KNOWLEDGE BASE CONTEXT

{retrieved_context}
"""
                }
            ] + chat_history
        }

        logger.info(
            "===== LLM PAYLOAD ====="
        )

        for msg in payload["messages"]:

            logger.info(
                f"{msg['role'].upper()}: "
                f"{msg['content'][:500]}"
            )

        reply = call_llm(
            payload,
            logger
        )

        store_assistant_message(
            session_id,
            reply
        )

        message_count = get_message_count(
            session_id
        )

        if (
            message_count > 0
            and message_count % MEMORY_CHUNK_SIZE == 0
        ):

            recent_chunk_messages = (
                fetch_recent_chat(
                    session_id,
                    MEMORY_CHUNK_SIZE
                )
            )

            create_memory_chunk(
                session_id,
                recent_chunk_messages
            )

        logger.info(
            "===== LLM RESPONSE ====="
        )

        logger.info(reply)

        logger.info(
            "===== QUERY TRACE END ====="
        )

        return {
            "reply": reply,
            "sources": sources,
            "llm_called": True,
            "hits_used": len(top_hits),
            "max_score": max_score,
            "attachments_used": len(attachment_ids)
        }

    except Exception as e:

        logger.error(str(e))

        return {
            "error": str(e)
        }