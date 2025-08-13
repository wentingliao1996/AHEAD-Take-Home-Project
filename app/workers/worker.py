import logging
import os
import re

from app.core.database import AsyncSessionLocal
from app.db.crud import get_user_files, update_task_status
from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

logger = logging.getLogger(__name__)

def bakeground_task() -> dict:
    """在背景任務中執行的程式碼"""
    try:
        return {"detail": '背景作業完成'}
    except Exception as e:
        logger.error(f"Background execution job error: {e}")
        return {"detail": "背景作業錯誤請查看Log"}

@celery_app.task(bind=True)
async def compute_stats(self, user_id: int):
    """計算用戶檔案統計的背景任務"""
    task_id = self.request.id
    
    logger.info(f"Task {task_id} - pending")
    self.update_state(state="PENDING")
    
    # 更新資料庫中的任務狀態
    db = AsyncSessionLocal()
    try:
        await update_task_status(db, task_id, "pending")
        
        logger.info(f"Task {task_id} - running")
        self.update_state(state="RUNNING")
        await update_task_status(db, task_id, "running")
        
        task_info = bakeground_task ()
        result = {
            "id":task_id,
            "userid": user_id,
            "taskinfo": task_info,
        }
        
        logger.info(f"Task {task_id} - finished")
        self.update_state(state="FINISHED")
        await update_task_status(db, task_id, "finished", str(result))
        
        return result
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        self.update_state(state="FAILURE")
        await update_task_status(db, task_id, "failed", str({"error": str(e)}))
        raise
    finally:
        await db.close()