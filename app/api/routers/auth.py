import logging
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import get_db
from app.db.crud import create_activity_log, create_user, get_user_by_email
from app.db.models import User
from app.deps import get_current_user
from app.schemas import Token, UserCreate, UserLogin
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 設置 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """用戶註冊"""
    # 檢查用戶是否已存在
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 創建新用戶
    hashed_password = pwd_context.hash(user_data.password)
    new_user = await create_user(db, email=user_data.email, hashed_password=hashed_password)
    
    # 生成訪問令牌
    access_token = create_access_token({"sub": new_user.email})
    
    # 記錄註冊活動
    await create_activity_log(
        db,
        user_id=new_user.id,
        username=new_user.email,
        activity_type="user_register",
        description="User registered successfully"
    )
    
    logger.info(f"New user registered: {new_user.email}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用戶登入"""
    # 驗證用戶憑證
    user = await get_user_by_email(db, user_data.email)
    if not user or not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號密碼錯誤")
    
    # 生成訪問令牌
    access_token = create_access_token({"sub": user.email}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # 記錄登入活動
    await create_activity_log(
        db,
        user_id=user.id,
        username=user.email,
        activity_type="user_login",
        description="User logged in successfully"
    )
    
    logger.info(f"User logged in: {user.email}")

    return {"access_token": access_token, "token_type": "bearer"}

