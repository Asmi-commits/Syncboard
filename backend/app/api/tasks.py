from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.board import Board, BoardMember, BoardRole
from app.models.task import Task, TaskColumn
from app.schemas.board import TaskCreate, TaskUpdate, TaskMove, TaskResponse
from app.core.websocket_manager import manager

router = APIRouter()


async def get_board_member(board_id: int, user: User, db: AsyncSession, min_role: BoardRole = BoardRole.MEMBER):
    result = await db.execute(select(Board).where(Board.id == board_id))
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if board.owner_id == user.id:
        return board
    result = await db.execute(
        select(BoardMember).where(BoardMember.board_id == board_id, BoardMember.user_id == user.id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a board member")
    role_order = {BoardRole.VIEWER: 0, BoardRole.MEMBER: 1, BoardRole.ADMIN: 2, BoardRole.OWNER: 3}
    if role_order[member.role] < role_order[min_role]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return board


async def load_task(task_id: int, db: AsyncSession) -> Task:
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.assignee), selectinload(Task.creator))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/boards/{board_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    board_id: int,
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_board_member(board_id, current_user, db)

    task = Task(**data.model_dump(), board_id=board_id, creator_id=current_user.id)
    db.add(task)
    await db.flush()
    task = await load_task(task.id, db)

    payload = {
        "type": "task_created",
        "task": {
            "id": task.id, "title": task.title,
            "column_id": task.column_id, "priority": task.priority,
            "position": task.position,
        }
    }
    await manager.broadcast_to_board(board_id, payload)
    return task


@router.get("/boards/{board_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_board_member(board_id, current_user, db)
    result = await db.execute(
        select(Task)
        .where(Task.board_id == board_id)
        .options(selectinload(Task.assignee), selectinload(Task.creator))
        .order_by(Task.column_id, Task.position)
    )
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task(task_id, db)
    await get_board_member(task.board_id, current_user, db)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task(task_id, db)
    await get_board_member(task.board_id, current_user, db)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    await db.flush()
    task = await load_task(task_id, db)

    await manager.broadcast_to_board(task.board_id, {
        "type": "task_updated",
        "task": {"id": task.id, "title": task.title, "column_id": task.column_id, "priority": task.priority}
    })
    return task


@router.post("/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: int,
    move: TaskMove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task(task_id, db)
    await get_board_member(task.board_id, current_user, db)

    # Validate column belongs to same board
    result = await db.execute(
        select(TaskColumn).where(TaskColumn.id == move.column_id, TaskColumn.board_id == task.board_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Column does not belong to this board")

    task.column_id = move.column_id
    task.position = move.position
    await db.flush()
    task = await load_task(task_id, db)

    await manager.broadcast_to_board(task.board_id, {
        "type": "task_moved",
        "task_id": task_id,
        "column_id": move.column_id,
        "position": move.position,
        "moved_by": current_user.username,
    })
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task(task_id, db)
    await get_board_member(task.board_id, current_user, db)
    board_id = task.board_id
    await db.delete(task)
    await db.flush()
    await manager.broadcast_to_board(board_id, {"type": "task_deleted", "task_id": task_id})
