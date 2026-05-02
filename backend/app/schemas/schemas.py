from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator

from app.models.models import UserRole, TaskStatus, TaskPriority


# ─── User Schemas ──────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Auth Schemas ──────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ─── Label Schemas ─────────────────────────────────────────────────────────────

class LabelCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class LabelResponse(LabelCreate):
    id: int

    class Config:
        from_attributes = True


# ─── Comment Schemas ───────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    author: UserResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Task Schemas ──────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    column_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    column_id: Optional[int] = None
    position: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    position: int
    due_date: Optional[datetime] = None
    column_id: int
    assignee: Optional[UserResponse] = None
    creator: UserResponse
    labels: List[LabelResponse] = []
    comments: List[CommentResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Board Column Schemas ──────────────────────────────────────────────────────

class ColumnCreate(BaseModel):
    title: str
    position: int = 0
    color: Optional[str] = None


class ColumnUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[int] = None
    color: Optional[str] = None


class ColumnResponse(BaseModel):
    id: int
    title: str
    position: int
    color: Optional[str] = None
    tasks: List[TaskResponse] = []

    class Config:
        from_attributes = True


# ─── Board Schemas ─────────────────────────────────────────────────────────────

class BoardMemberResponse(BaseModel):
    id: int
    user: UserResponse
    role: UserRole
    joined_at: datetime

    class Config:
        from_attributes = True


class BoardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    color: str = "#6366f1"
    is_public: bool = False


class BoardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_public: Optional[bool] = None


class BoardResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    color: str
    is_public: bool
    owner: UserResponse
    members: List[BoardMemberResponse] = []
    columns: List[ColumnResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BoardSummary(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    color: str
    is_public: bool
    owner: UserResponse
    member_count: int = 0
    task_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ─── WebSocket Schemas ─────────────────────────────────────────────────────────

class WSEvent(BaseModel):
    type: str
    board_id: int
    data: dict
    user_id: int
    timestamp: datetime = None

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


# ─── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int
