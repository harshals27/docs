import os
import tempfile

from fastapi import (
    APIRouter,
    File,
    Form,
    UploadFile,
    HTTPException
)

from app.services.attachment_service import (
    ingest_attachment,
    delete_attachment,
    get_attachment_metadata,
    attachment_exists
)

router = APIRouter(
    prefix="/attachments",
    tags=["attachments"]
)


@router.post("/upload")
async def upload_attachment(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload, parse, chunk, embed,
    and index a document.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename missing."
        )

    suffix = os.path.splitext(
        file.filename
    )[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp_file:

        content = await file.read()

        temp_file.write(content)

        temp_path = temp_file.name

    try:

        result = ingest_attachment(
            session_id=session_id,
            temp_file_path=temp_path,
            original_filename=file.filename
        )

        return {
            "success": True,
            "attachment": result
        }

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.delete("/{attachment_id}")
def remove_attachment(
    attachment_id: str
):
    """
    Delete all indexed chunks
    belonging to an attachment.
    """

    if not attachment_exists(
        attachment_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Attachment not found."
        )

    delete_attachment(
        attachment_id
    )

    return {
        "success": True,
        "attachment_id": attachment_id,
        "message": "Attachment deleted successfully."
    }


@router.get("/{attachment_id}")
def get_attachment(
    attachment_id: str
):
    """
    Retrieve attachment metadata.
    """

    metadata = get_attachment_metadata(
        attachment_id
    )

    if not metadata:
        raise HTTPException(
            status_code=404,
            detail="Attachment not found."
        )

    return metadata