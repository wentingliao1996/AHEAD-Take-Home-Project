from datetime import datetime
from typing import List

from app.db.models import ActivityLog, FileInfo, TaskRecord, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# user
async def create_user(db: AsyncSession, email: str, hashed_password: str) -> User:
    usrinfo = User(email=email, hashed_password=hashed_password)
    db.add(usrinfo)
    await db.commit()
    await db.refresh(usrinfo)
    return usrinfo

async def get_user_by_email(db: AsyncSession, email: str):
    q = await db.execute(select(User).where(User.email == email))
    return q.scalars().first()

# file
async def create_file(db: AsyncSession, **kwargs) -> FileInfo:
    f = FileInfo(**kwargs)
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f

async def get_file_by_slug(db: AsyncSession, slug: str):
    q = await db.execute(select(FileInfo).where(FileInfo.slug == slug))
    return q.scalars().first()

async def get_user_files(db: AsyncSession, user_id: int) -> List[FileInfo]:
    q = await db.execute(select(FileInfo).where(FileInfo.owner_id == user_id))
    return q.scalars().all()

async def get_public_files(db: AsyncSession) -> List[FileInfo]:
    q = await db.execute(select(FileInfo).where(FileInfo.is_public == True))
    return q.scalars().all()

# log
async def get_user_activities(db: AsyncSession, user_id: int) -> List[ActivityLog]:
    q = await db.execute(select(ActivityLog).where(ActivityLog.user_id == user_id).order_by(ActivityLog.timestamp.desc()))
    return q.scalars().all()

async def create_activity_log(db: AsyncSession, **kwargs) -> ActivityLog:
    log = ActivityLog(**kwargs)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log