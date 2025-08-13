from datetime import datetime
from typing import List

from app.db.models import ActivityLog, FileInfo, TaskRecord, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user(db: AsyncSession, email: str, hashed_password: str) -> User:
    usrinfo = User(email=email, hashed_password=hashed_password)
    db.add(usrinfo)
    await db.commit()
    await db.refresh(usrinfo)
    return usrinfo

async def get_user_by_email(db: AsyncSession, email: str):
    q = await db.execute(select(User).where(User.email == email))
    return q.scalars().first()

async def get_user_activities(db: AsyncSession, user_id: int) -> List[ActivityLog]:
    q = await db.execute(select(ActivityLog).where(ActivityLog.user_id == user_id).order_by(ActivityLog.timestamp.desc()))
    return q.scalars().all()
    
def get_fcs_version(path: str) -> str:
    fd = flowio.FlowData(path)
    return fd.version