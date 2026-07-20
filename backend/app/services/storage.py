import os

from fastapi import HTTPException, UploadFile, status

from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def validate_upload_batch(existing_count: int, files: list[UploadFile]) -> list[tuple[str, bytes]]:
    """Validate file count/type/size for a batch of uploads and return (filename, content) pairs.

    Raises HTTPException(400) on the first violation. Reads file contents up front so nothing
    is written to disk if any file in the batch is rejected.
    """
    if existing_count + len(files) > settings.max_files_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A request may have at most {settings.max_files_per_request} documents",
        )

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    validated: list[tuple[str, bytes]] = []
    for upload in files:
        filename = os.path.basename(upload.filename or "")
        extension = os.path.splitext(filename)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type for '{filename}'. Allowed types: PDF, JPG, PNG",
            )

        content = upload.file.read()
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' exceeds the maximum size of {settings.max_file_size_mb}MB",
            )

        validated.append((filename, content))

    return validated


def save_request_document(request_id: int, filename: str, content: bytes) -> tuple[str, int]:
    """Save file content to disk under `{upload_dir}/{request_id}/{filename}` and return (path, size)."""
    request_dir = os.path.join(settings.upload_dir, str(request_id))
    os.makedirs(request_dir, exist_ok=True)

    file_path = os.path.join(request_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, len(content)
