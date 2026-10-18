from app.services.elasticsearch_service import (
    save_chat_message,
    get_recent_messages,
    count_messages
)


def store_user_message(
    session_id,
    query
):
    save_chat_message(
        session_id,
        "user",
        query
    )


def store_assistant_message(
    session_id,
    answer
):
    save_chat_message(
        session_id,
        "assistant",
        answer
    )


def fetch_recent_chat(
    session_id,
    limit=10
):
    return get_recent_messages(
        session_id,
        limit
    )


def get_message_count(
    session_id
):
    return count_messages(session_id)