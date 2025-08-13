from app.core.database import get_db
from app.db.crud import get_user_files
from app.db.models import User
from app.deps import get_current_user
from app.schemas import TaskCreateResp, TaskStatus
from app.workers.worker import celery_app, compute_stats
from celery.result import AsyncResult
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.post("/tasks", response_model=TaskCreateResp)
def create_stats_task(current_user: User = Depends(get_current_user)):
    """創建背景計算任務"""
    task = compute_stats.delay(user_id=current_user.id)
    return {"task_id": task.id, "status": "PENDING"}

@router.get("/tasks/{task_id}", response_model=TaskStatus)
def get_task_status(task_id: str):
    """獲取任務狀態和結果"""
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id, 
        "status": task.status, 
        "result": task.result if task.successful() else None
    }

@router.get("/user/all_fcs_info")
async def get_user_all_fcs_info(current_user: User = Depends(get_current_user)):
    """獲取用戶所有FCS檔案資訊"""
    
    db = await get_db().__anext__()
    user_files = await get_user_files(db, current_user.id)
    
    return {
        "files": [
            {
                "filename": f.original_filename,
                "size_bytes": float(f.size_bytes),
                "uploaded_at": f.uploaded_at,
                "fcs_version": f.fcs_version,
                "is_public": f.is_public
            }
            for f in user_files
        ]
    }

@router.get("/user/files_statistics")
async def get_user_fcs_statistics(current_user: User = Depends(get_current_user)):
    """獲取用戶檔案統計"""
    
    db = await get_db().__anext__()
    user_files = await get_user_files(db, current_user.id)
    
    total_size = sum(float(f.size_bytes) for f in user_files)
    
    return {
        "total_files": len(user_files),
        "total_size_bytes": total_size
    }