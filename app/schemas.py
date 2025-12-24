from pydantic import BaseModel
from fastapi_users import schemas
import uuid
from typing import Optional
class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    title: str
    content: str

class ProfilePageRead(BaseModel):
    url: str
    file_type: str
    file_name: str

    class Config:
        from_attributes = True

class UserRead(schemas.BaseUser[uuid.UUID]):
    profile_page: Optional[ProfilePageRead] = None

    class Config:
        from_attributes = True
class UserCreate(schemas.BaseUserCreate):
    pass
class UserUpdate(schemas.BaseUserUpdate):
    pass