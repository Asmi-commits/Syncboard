from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.models import Board, BoardMember, BoardColumn, Task, UserRole
from app.schemas.schemas import BoardCreate, BoardUpdate, ColumnCreate


async def get_board_with_details(db: AsyncSession, board_id: int) -> Optional[Board]:
    result = await db.execute(
        select(Board)
        .options(
            selectinload(Board.owner),
            selectinload(Board.members).selectinload(BoardMember.user),
            selectinload(Board.columns)
            .selectinload(BoardColumn.tasks)
            .selectinload(Task.assignee),
            selectinload(Board.columns)
            .selectinload(BoardColumn.tasks)
            .selectinload(Task.creator),
            selectinload(Board.columns)
            .selectinload(BoardColumn.tasks)
            .selectinload(Task.labels),
            selectinload(Board.columns)
            .selectinload(BoardColumn.tasks)
            .selectinload(Task.comments),
        )
        .where(Board.id == board_id)
    )
    return result.scalar_one_or_none()


async def get_user_boards(db: AsyncSession, user_id: int) -> List[Board]:
    # Boards owned by user or member of
    owned = await db.execute(
        select(Board)
        .options(selectinload(Board.owner), selectinload(Board.members))
        .where(Board.owner_id == user_id)
    )
    member_board_ids_q = await db.execute(
        select(BoardMember.board_id).where(BoardMember.user_id == user_id)
    )
    member_board_ids = [r[0] for r in member_board_ids_q.fetchall()]

    member_boards = []
    if member_board_ids:
        mb_result = await db.execute(
            select(Board)
            .options(selectinload(Board.owner), selectinload(Board.members))
            .where(Board.id.in_(member_board_ids), Board.owner_id != user_id)
        )
        member_boards = list(mb_result.scalars().all())

    all_boards = list(owned.scalars().all()) + member_boards
    return all_boards


async def create_board(db: AsyncSession, board_data: BoardCreate, owner_id: int) -> Board:
    board = Board(
        title=board_data.title,
        description=board_data.description,
        color=board_data.color,
        is_public=board_data.is_public,
        owner_id=owner_id,
    )
    db.add(board)
    await db.flush()

    # Create default columns
    default_columns = [
        {"title": "To Do", "position": 0, "color": "#64748b"},
        {"title": "In Progress", "position": 1, "color": "#3b82f6"},
        {"title": "Review", "position": 2, "color": "#f59e0b"},
        {"title": "Done", "position": 3, "color": "#22c55e"},
    ]
    for col_data in default_columns:
        col = BoardColumn(board_id=board.id, **col_data)
        db.add(col)

    await db.flush()
    return await get_board_with_details(db, board.id)


async def update_board(db: AsyncSession, board: Board, update_data: BoardUpdate) -> Board:
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(board, field, value)
    await db.flush()
    return await get_board_with_details(db, board.id)


async def delete_board(db: AsyncSession, board: Board):
    await db.delete(board)
    await db.flush()


async def add_member(
    db: AsyncSession, board_id: int, user_id: int, role: UserRole = UserRole.MEMBER
) -> BoardMember:
    member = BoardMember(board_id=board_id, user_id=user_id, role=role)
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def check_board_access(
    db: AsyncSession, board_id: int, user_id: int
) -> Optional[str]:
    """Returns role string if user has access, None otherwise"""
    board_result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    board = board_result.scalar_one_or_none()
    if not board:
        return None

    if board.owner_id == user_id:
        return "admin"

    member_result = await db.execute(
        select(BoardMember).where(
            BoardMember.board_id == board_id,
            BoardMember.user_id == user_id,
        )
    )
    member = member_result.scalar_one_or_none()
    if member:
        return member.role.value

    if board.is_public:
        return "viewer"

    return None


async def create_column(
    db: AsyncSession, board_id: int, col_data: ColumnCreate
) -> BoardColumn:
    col = BoardColumn(
        board_id=board_id,
        title=col_data.title,
        position=col_data.position,
        color=col_data.color,
    )
    db.add(col)
    await db.flush()
    await db.refresh(col)
    return col
