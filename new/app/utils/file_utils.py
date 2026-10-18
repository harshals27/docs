import hashlib
import os
import shutil
import uuid

from pathlib import Path

from app.config import (
    UPLOAD_ROOT,
    UPLOAD_ORIGINALS_DIR,
    UPLOAD_PROCESSED_DIR
)


def ensure_upload_directories():
    """
    Create upload directories if they do not exist.
    """

    Path(UPLOAD_ROOT).mkdir(
        parents=True,
        exist_ok=True
    )

    Path(UPLOAD_ORIGINALS_DIR).mkdir(
        parents=True,
        exist_ok=True
    )

    Path(UPLOAD_PROCESSED_DIR).mkdir(
        parents=True,
        exist_ok=True
    )


def sanitize_filename(filename: str) -> str:
    """
    Remove unsafe characters from filenames.
    """

    safe_name = os.path.basename(filename)

    safe_name = (
        safe_name
        .replace(" ", "_")
        .replace("..", "")
        .replace("/", "")
        .replace("\\", "")
    )

    return safe_name


def generate_attachment_id() -> str:
    """
    Generate unique attachment id.
    """

    return str(uuid.uuid4())


def calculate_file_hash(file_path: str) -> str:
    """
    Generate SHA256 hash for a file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        for chunk in iter(
            lambda: file.read(4096),
            b""
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


def save_uploaded_file(
    source_path: str,
    original_filename: str
):
    """
    Save uploaded file and return metadata.
    """

    ensure_upload_directories()

    attachment_id = generate_attachment_id()

    safe_filename = sanitize_filename(
        original_filename
    )

    extension = Path(
        safe_filename
    ).suffix.lower()

    stored_filename = (
        f"{attachment_id}{extension}"
    )

    destination_path = os.path.join(
        UPLOAD_ORIGINALS_DIR,
        stored_filename
    )

    shutil.copyfile(
        source_path,
        destination_path
    )

    file_hash = calculate_file_hash(
        destination_path
    )

    return {
        "attachment_id": attachment_id,
        "original_filename": safe_filename,
        "stored_filename": stored_filename,
        "file_path": destination_path,
        "file_hash": file_hash
    }


def delete_file(file_path: str) -> bool:
    """
    Delete a file if it exists.
    """

    try:

        if os.path.exists(file_path):
            os.remove(file_path)

        return True

    except Exception:

        return False