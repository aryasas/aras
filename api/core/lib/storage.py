import os
import uuid
from fastapi import UploadFile
from ..base.service import Service

class StorageService(Service):
    """
    Handles local file storage for the Aras framework.
    """
    UPLOAD_DIR = "storage/uploads"

    @classmethod
    def save_file(cls, file: UploadFile) -> dict:
        """Saves an uploaded file and returns metadata."""
        if not os.path.exists(cls.UPLOAD_DIR):
            os.makedirs(cls.UPLOAD_DIR, exist_ok=True)

        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{ext}"
        path = os.path.join(cls.UPLOAD_DIR, filename)

        with open(path, "wb") as f:
            f.write(file.file.read())

        return {
            "id": file_id,
            "filename": file.filename,
            "stored_name": filename,
            "mime_type": file.content_type,
            "size": os.path.getsize(path),
            "url": f"/api/files/download/{filename}"
        }

    @classmethod
    def get_file_path(cls, filename: str) -> str:
        return os.path.join(cls.UPLOAD_DIR, filename)
