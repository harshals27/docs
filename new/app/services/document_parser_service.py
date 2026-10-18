import os

import pandas as pd
import pdfplumber

from docx import Document


def parse_pdf(file_path: str) -> str:
    """
    Extract text from PDF.
    """

    extracted_text = []

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                extracted_text.append(page_text)

    return "\n".join(extracted_text)


def parse_docx(file_path: str) -> str:
    """
    Extract text from DOCX.
    """

    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            paragraphs.append(
                paragraph.text
            )

    return "\n".join(paragraphs)


def parse_txt(file_path: str) -> str:
    """
    Extract text from text files.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:

        return file.read()


def parse_csv(file_path: str) -> str:
    """
    Extract text from CSV files.
    """

    df = pd.read_csv(file_path)

    return df.astype(str).to_string(
        index=False
    )


def parse_document(file_path: str) -> str:
    """
    Detect file type and extract text.
    """

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension == ".pdf":
        return parse_pdf(file_path)

    if extension == ".docx":
        return parse_docx(file_path)

    if extension == ".txt":
        return parse_txt(file_path)

    if extension == ".csv":
        return parse_csv(file_path)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


def chunk_text(
    text: str,
    chunk_size: int,
    overlap: int
):
    """
    Split text into overlapping chunks.
    """

    if not text:
        return []

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        if chunk.strip():
            chunks.append(chunk)

        start += (
            chunk_size - overlap
        )

    return chunks
