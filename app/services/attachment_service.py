from datetime import datetime
import os

from app.config import (
    INDEX_NAME,
    ATTACHMENT_CHUNK_SIZE,
    ATTACHMENT_CHUNK_OVERLAP
)

from app.services.document_parser_service import (
    parse_document,
    chunk_text
)

from app.services.embedding_service import (
    get_embeddings
)

from app.services.elasticsearch_service import (
    es
)

from app.utils.file_utils import (
    save_uploaded_file
)


def index_attachment_chunks(
    session_id,
    attachment_id,
    filename,
    chunks,
    embeddings
):
    """
    Store document chunks in Elasticsearch.
    """

    indexed_count = 0

    for idx, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):

        document = {
            "attachment_id": attachment_id,
            "session_id": session_id,
            "source_file": filename,
            "filename": filename,
            "chunk_number": idx + 1,
            "combined": chunk,
            "embedding": embedding,
            "created_at": (
                datetime.utcnow().isoformat()
            )
        }

        es.index(
            index=INDEX_NAME,
            document=document
        )

        indexed_count += 1

    return indexed_count


def ingest_attachment(
    session_id,
    temp_file_path,
    original_filename
):
    """
    Complete attachment ingestion pipeline.

    Upload
        -> Save
        -> Parse
        -> Chunk
        -> Embed
        -> Index
    """

    file_info = save_uploaded_file(
        temp_file_path,
        original_filename
    )

    attachment_id = file_info[
        "attachment_id"
    ]

    stored_path = file_info[
        "file_path"
    ]

    extracted_text = parse_document(
        stored_path
    )

    if not extracted_text.strip():

        raise ValueError(
            "No text could be extracted from file."
        )

    chunks = chunk_text(
        extracted_text,
        ATTACHMENT_CHUNK_SIZE,
        ATTACHMENT_CHUNK_OVERLAP
    )

    if not chunks:

        raise ValueError(
            "No searchable chunks generated."
        )

    embeddings = get_embeddings(
        chunks
    )

    indexed_count = index_attachment_chunks(
        session_id=session_id,
        attachment_id=attachment_id,
        filename=original_filename,
        chunks=chunks,
        embeddings=embeddings
    )

    return {
        "attachment_id": attachment_id,
        "filename": original_filename,
        "file_hash": file_info["file_hash"],
        "stored_filename": file_info[
            "stored_filename"
        ],
        "chunk_count": indexed_count,
        "status": "indexed"
    }


def delete_attachment(
    attachment_id
):
    """
    Delete all chunks belonging
    to an attachment.
    """

    response = es.delete_by_query(
        index=INDEX_NAME,
        query={
            "term": {
                "attachment_id": attachment_id
            }
        }
    )

    return response


def get_attachment_chunks(
    attachment_id,
    limit=100
):
    """
    Fetch indexed chunks.
    """

    response = es.search(
        index=INDEX_NAME,
        query={
            "term": {
                "attachment_id": attachment_id
            }
        },
        size=limit
    )

    return [
        hit["_source"]
        for hit in response["hits"]["hits"]
    ]


def attachment_exists(
    attachment_id
):
    """
    Check if attachment exists.
    """

    response = es.search(
        index=INDEX_NAME,
        query={
            "term": {
                "attachment_id": attachment_id
            }
        },
        size=1
    )

    return (
        response["hits"]["total"]["value"]
        > 0
    )


def get_attachment_metadata(
    attachment_id
):
    """
    Return attachment metadata.
    """

    response = es.search(
        index=INDEX_NAME,
        query={
            "term": {
                "attachment_id": attachment_id
            }
        },
        size=1
    )

    hits = response["hits"]["hits"]

    if not hits:
        return None

    source = hits[0]["_source"]

    return {
        "attachment_id": source[
            "attachment_id"
        ],
        "filename": (
            source.get("source_file")
            or source.get("filename")
        ),
        "session_id": source[
            "session_id"
        ],
        "created_at": source[
            "created_at"
        ]
    }