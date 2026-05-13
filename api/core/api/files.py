from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import Any
from ..lib.storage import StorageService
from ..auth.service import get_current_user

router = APIRouter(prefix="/files", tags=["File Management"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    _: Any = Depends(get_current_user)
):
    """Standardized file upload endpoint."""
    try:
        return StorageService.save_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/download/{filename}")
async def download_file(filename: str):
    """Standardized file download endpoint."""
    path = StorageService.get_file_path(filename)
    import os
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
