import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User
from app.models.board import Board, BoardMember, BoardRole
from app.models.task import Task, TaskColumn

TEST_DB = "sqlite+aiosqlite:///./test_syncboard.db"

test_engine = create_async_engine(TEST_DB, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        yield session
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest.fixture
async def db_session(db: AsyncSession) -> AsyncSession:
    return db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    user = User(
        email="testuser@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=hash_password("password123"),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_user2(db: AsyncSession) -> User:
    user = User(
        email="testuser2@example.com",
        username="testuser2",
        full_name="Test User 2",
        hashed_password=hash_password("password123"),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_board(db: AsyncSession, test_user: User) -> Board:
    board = Board(
        name="Test Board",          # Board uses `name` not `title`
        description="A board for testing",
        color="#6366f1",
        owner_id=test_user.id,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    for i, col_name in enumerate(["To Do", "In Progress", "Done"]):
        col = TaskColumn(board_id=board.id, name=col_name, position=i)
        db.add(col)
    await db.commit()
    return board


@pytest.fixture
async def test_column(db: AsyncSession, test_board: Board) -> TaskColumn:
    from sqlalchemy import select
    result = await db.execute(
        select(TaskColumn).where(TaskColumn.board_id == test_board.id).limit(1)
    )
    return result.scalar_one()


@pytest.fixture
async def test_task(db: AsyncSession, test_column: TaskColumn, test_user: User, test_board: Board) -> Task:
    task = Task(
        title="Test Task",
        description="A task for testing",
        board_id=test_board.id,     # required FK
        column_id=test_column.id,
        creator_id=test_user.id,    # Task uses `creator_id` not `created_by_id`
        position=0,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers2(test_user2: User) -> dict:
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(test_user2.id)})
    return {"Authorization": f"Bearer {token}"}
