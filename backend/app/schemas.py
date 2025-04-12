from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# Tag schemas
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    
    class Config:
        orm_mode = True

# Message schemas
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    tags: Optional[List[str]] = []

class Message(MessageBase):
    id: int
    user_id: int
    created_at: datetime
    tags: List[Tag] = []
    like_count: int = 0
    
    class Config:
        orm_mode = True

class MessageWithUser(Message):
    username: str
    
    class Config:
        orm_mode = True

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserWithMessages(User):
    messages: List[Message] = []
    
    class Config:
        orm_mode = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Like schemas
class LikeCreate(BaseModel):
    message_id: int

class Like(BaseModel):
    user_id: int
    message_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str
    data: dict