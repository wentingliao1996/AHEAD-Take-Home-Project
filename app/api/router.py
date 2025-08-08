from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute("SELECT * FROM users;")
    return result.fetchall()
