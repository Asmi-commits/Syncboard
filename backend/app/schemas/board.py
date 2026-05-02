from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.board import BoardRole
from app.models.task import TaskPriority
from app.schemas.user import UserResponse


# ─── Column Schemas ───────────────────────────────────────────────────────────

class ColumnCreate(BaseModel):
    name: str
    color: str = "#64748b"
    position: int = 0


class ColumnUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    position: Optional[int] = None


class ColumnResponse(BaseModel):
    id: int
    name: str
    position: int
    color: str
    board_id: int

    model_config = {"from_attributes": True}


# ─── Board Schemas ────────────────────────────────────────────────────────────

class BoardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#6366f1"


class BoardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_archived: Optional[bool] = None


class BoardMemberResponse(BaseModel):
    id: int
    user: UserResponse
    role: BoardRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class BoardResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    is_archived: bool
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    members: List[BoardMemberResponse] = []
    columns: List[ColumnResponse] = []

    model_config = {"from_attributes": True}


class BoardInvite(BaseModel):
    user_id: int
    role: BoardRole = BoardRole.MEMBER


# ─── Task Schemas ─────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    column_id: Optional[int] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    position: int = 0


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    column_id: Optional[int] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    position: Optional[int] = None
    is_completed: Optional[bool] = None


class TaskMove(BaseModel):
    column_id: int
    position: int


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: TaskPriority
    position: int
    is_completed: bool
    due_date: Optional[datetime]
    board_id: int
    column_id: Optional[int]
    assignee: Optional[UserResponse]
    creator: UserResponse
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
