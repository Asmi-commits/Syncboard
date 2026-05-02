from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.models import Task, Comment, TaskLabel, BoardColumn
from app.schemas.schemas import TaskCreate, TaskUpdate, CommentCreate, LabelCreate


async def get_task_with_details(db: AsyncSession, task_id: int) -> Optional[Task]:
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.assignee),
            selectinload(Task.creator),
            selectinload(Task.labels),
            selectinload(Task.comments).selectinload(Comment.author),
        )
        .where(Task.id == task_id)
    )
    return result.scalar_one_or_none()


async def create_task(
    db: AsyncSession, task_data: TaskCreate, created_by_id: int
) -> Task:
    # Get max position in column
    pos_result = await db.execute(
        select(Task).where(Task.column_id == task_data.column_id)
    )
    existing = pos_result.scalars().all()
    position = max((t.position for t in existing), default=-1) + 1

    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
        assignee_id=task_data.assignee_id,
        column_id=task_data.column_id,
        created_by_id=created_by_id,
        position=position,
    )
    db.add(task)
    await db.flush()
    return await get_task_with_details(db, task.id)


async def update_task(
    db: AsyncSession, task: Task, update_data: TaskUpdate
) -> Task:
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.flush()
    return await get_task_with_details(db, task.id)


async def delete_task(db: AsyncSession, task: Task):
    await db.delete(task)
    await db.flush()


async def add_comment(
    db: AsyncSession, task_id: int, author_id: int, comment_data: CommentCreate
) -> Comment:
    comment = Comment(
        content=comment_data.content,
        task_id=task_id,
        author_id=author_id,
    )
    db.add(comment)
    await db.flush()

    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.id == comment.id)
    )
    return result.scalar_one()


async def add_label(
    db: AsyncSession, task_id: int, label_data: LabelCreate
) -> TaskLabel:
    label = TaskLabel(
        name=label_data.name,
        color=label_data.color,
        task_id=task_id,
    )
    db.add(label)
    await db.flush()
    await db.refresh(label)
    return label


async def get_column_board_id(db: AsyncSession, column_id: int) -> Optional[int]:
    result = await db.execute(
        select(BoardColumn.board_id).where(BoardColumn.id == column_id)
    )
    row = result.first()
    return row[0] if row else None
