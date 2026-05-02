from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.board import Board, BoardMember, BoardRole
from app.models.task import TaskColumn
from app.schemas.board import (
    BoardCreate, BoardUpdate, BoardResponse,
    BoardInvite, ColumnCreate, ColumnUpdate, ColumnResponse
)
from app.core.websocket_manager import manager

router = APIRouter()


async def get_board_or_404(board_id: int, db: AsyncSession) -> Board:
    result = await db.execute(
        select(Board)
        .where(Board.id == board_id)
        .options(
            selectinload(Board.members).selectinload(BoardMember.user),
            selectinload(Board.columns),
        )
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


async def check_board_access(board: Board, user: User, min_role: BoardRole = BoardRole.VIEWER):
    if board.owner_id == user.id:
        return
    member = next((m for m in board.members if m.user_id == user.id), None)
    if not member:
        raise HTTPException(status_code=403, detail="Not a board member")
    role_order = {BoardRole.VIEWER: 0, BoardRole.MEMBER: 1, BoardRole.ADMIN: 2, BoardRole.OWNER: 3}
    if role_order[member.role] < role_order[min_role]:
        raise HTTPException(status_code=403, detail="Insufficient board permissions")


@router.post("/", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    data: BoardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = Board(**data.model_dump(), owner_id=current_user.id)
    db.add(board)
    await db.flush()

    # Add default columns
    default_columns = [
        TaskColumn(name="To Do", position=0, color="#64748b", board_id=board.id),
        TaskColumn(name="In Progress", position=1, color="#3b82f6", board_id=board.id),
        TaskColumn(name="Review", position=2, color="#f59e0b", board_id=board.id),
        TaskColumn(name="Done", position=3, color="#22c55e", board_id=board.id),
    ]
    for col in default_columns:
        db.add(col)

    await db.flush()
    await db.refresh(board)
    return await get_board_or_404(board.id, db)


@router.get("/", response_model=List[BoardResponse])
async def list_boards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Boards owned by user OR boards where user is a member
    owned = await db.execute(
        select(Board)
        .where(Board.owner_id == current_user.id, Board.is_archived == False)
        .options(
            selectinload(Board.members).selectinload(BoardMember.user),
            selectinload(Board.columns),
        )
    )
    member_of = await db.execute(
        select(Board)
        .join(BoardMember, BoardMember.board_id == Board.id)
        .where(BoardMember.user_id == current_user.id, Board.is_archived == False)
        .options(
            selectinload(Board.members).selectinload(BoardMember.user),
            selectinload(Board.columns),
        )
    )
    boards = {b.id: b for b in owned.scalars().all()}
    boards.update({b.id: b for b in member_of.scalars().all()})
    return list(boards.values())


@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = await get_board_or_404(board_id, db)
    await check_board_access(board, current_user)
    return board


@router.patch("/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: int,
    data: BoardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = await get_board_or_404(board_id, db)
    await check_board_access(board, current_user, BoardRole.ADMIN)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(board, field, value)
    await db.flush()
    updated = await get_board_or_404(board_id, db)

    await manager.broadcast_to_board(board_id, {
        "type": "board_updated",
        "board": {"id": board_id, "name": updated.name, "color": updated.color}
    })
    return updated


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = await get_board_or_404(board_id, db)
    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete board")
    await db.delete(board)


@router.post("/{board_id}/members", response_model=BoardResponse)
async def invite_member(
    board_id: int,
    invite: BoardInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = await get_board_or_404(board_id, db)
    await check_board_access(board, current_user, BoardRole.ADMIN)

    # Check user exists
    result = await db.execute(select(User).where(User.id == invite.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check not already a member
    existing = next((m for m in board.members if m.user_id == invite.user_id), None)
    if existing or board.owner_id == invite.user_id:
        raise HTTPException(status_code=400, detail="User already a member")

    member = BoardMember(board_id=board_id, user_id=invite.user_id, role=invite.role)
    db.add(member)
    await db.flush()
    db.expire(board)
    return await get_board_or_404(board_id, db)


@router.delete("/{board_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    board_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = await get_board_or_404(board_id, db)
    await check_board_access(board, current_user, BoardRole.ADMIN)
    member = next((m for m in board.members if m.user_id == user_id), None)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)


# ─── Columns ─────────────────────────────────────────────────────────────────

@router.post("/{board_id}/columns", response_model=ColumnResponse, status_code=201)
async def create_column(
    board_id: int,
    data: ColumnCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = await get_board_or_404(board_id, db)
    await check_board_access(board, current_user, BoardRole.MEMBER)
    col = TaskColumn(**data.model_dump(), board_id=board_id)
    db.add(col)
    await db.flush()
    await db.refresh(col)
    await manager.broadcast_to_board(board_id, {"type": "column_created", "column": {"id": col.id, "name": col.name}})
    return col


@router.patch("/{board_id}/columns/{col_id}", response_model=ColumnResponse)
async def update_column(
    board_id: int,
    col_id: int,
    data: ColumnUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = await get_board_or_404(board_id, db)
    await check_board_access(board, current_user, BoardRole.MEMBER)
    result = await db.execute(select(TaskColumn).where(TaskColumn.id == col_id, TaskColumn.board_id == board_id))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(col, field, value)
    await db.flush()
    await db.refresh(col)
    return col


@router.delete("/{board_id}/columns/{col_id}", status_code=204)
async def delete_column(
    board_id: int,
    col_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    board = await get_board_or_404(board_id, db)
    await check_board_access(board, current_user, BoardRole.ADMIN)
    result = await db.execute(select(TaskColumn).where(TaskColumn.id == col_id, TaskColumn.board_id == board_id))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    await db.delete(col)
