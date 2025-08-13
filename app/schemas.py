from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    class Config:
        orm_mode = True

class FileUploadResponse(BaseModel):
    filename: str
    size: float
    uploaded_at: datetime = datetime.utcnow()
    fcs_version: Optional[str]
    is_public: bool
    owner_id: Optional[int]
    class Config:
        orm_mode = True