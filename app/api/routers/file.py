import logging
import os
import shutil
import time
from pathlib import Path
from typing import Optional

import shortuuid
from app.api.utils import get_fcs_version
from app.core.config import settings
from app.core.database import get_db
from app.db.crud import (
    create_activity_log,
    create_file,
    get_file_by_slug,
    get_public_files,
    get_user_files,
)
from app.db.models import User
from app.deps import get_current_user, get_current_user_optional
from app.schemas import FileUploadResponse
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/files", tags=["Files"])


UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = [".fcs"]
chunk_size = 1024 * 1024

# 設置 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    is_public: bool = Form(True),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """上傳檔案 - 支援公開和私人上傳"""
    start_time = time.time()

    # 驗證檔案格式
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file format. Only FCS files are allowed.")
    
    # 驗證檔案大小
    file_size = 0
    temp_file_path = f"/tmp/{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > settings.MAX_FILE_MB * 1024 * 1024:
                    raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.")
                buffer.write(chunk)
        
        fcs_version = get_fcs_version(temp_file_path)
        
        # 生成唯一檔名和短連結
        stored_filename = f"{shortuuid.uuid()}_{file.filename}"
        slug = shortuuid.uuid()[:8]
        
        # 創建檔案記錄
        file_data = {
            "original_filename": file.filename,
            "stored_filename": stored_filename,
            "size_bytes": file_size,
            "fcs_version": fcs_version,
            "is_public": is_public,
            "slug": slug
        }
        
        if current_user:
            file_data["owner_id"] = current_user.id
        else:
            file_data["owner_id"] = 0

        # 移動檔案到永久儲存位置
        final_path = os.path.join(settings.UPLOAD_DIR, stored_filename)
        shutil.move(temp_file_path, final_path)
        
        # 記錄活動
        if current_user:
            await create_activity_log(
                db,
                user_id=current_user.id,
                username=current_user.email,
                activity_type="file_upload",
                description=f"Uploaded file: {file.filename} ({'public' if is_public else 'private'})"
            )
        
        # 計算總上傳時間
        total_time = time.time() - start_time
        logger.info(f"File uploaded in {total_time:.2f} seconds - Size: {file_size} bytes, User: {current_user.email if current_user else 'anonymous'}")
        print(file_data)
        new_file = await create_file(db,**file_data)

        return FileUploadResponse(
            short_link=f"/files/{slug}",
            filename=file.filename,
            size=file_size,
            fcs_version=fcs_version,
            is_public=is_public,
            owner_id = file_data["owner_id"]
        )
        
    except Exception as e:
        # 清理臨時檔案
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/files")
async def get_file(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """獲取公開+私人檔案"""

    pulic_file = await get_public_files(db)

    if current_user:
        owner_file = await get_user_files(db, current_user.id)
        await create_activity_log(
            db,
            user_id=current_user.id,
            username=current_user.email,
            activity_type="file_access",
            description=f"{current_user.id}get all file"
        )
        return pulic_file+owner_file
    
    await create_activity_log(
            db,
            user_id=current_user.id,
            username=current_user.email,
            activity_type="file_access",
            description=f"get all public file"
        )
    return pulic_file
    

@router.put("/{slug}/visibility")
async def update_file_visibility(
    slug: str,
    is_public: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新檔案為私人（僅檔案擁有者）"""
    if not current_user:
        raise HTTPException(status_code=403, detail="Please login")
   
    file_record = await get_file_by_slug(db, slug)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if current_user.id != file_record.owner_id:
        raise HTTPException(status_code=403, detail="Only file owner can change visibility")
    
    file_record.is_public = is_public
    db.add(file_record)
    await db.commit()
    
    # 記錄活動
    await create_activity_log(
        db,
        user_id=current_user.id,
        username=current_user.email,
        activity_type="file_visibility_change",
        description=f"Changed file visibility to {'public' if is_public else 'private'}: {file_record.original_filename}"
    )
    
    return {"message": "File visibility updated successfully"}