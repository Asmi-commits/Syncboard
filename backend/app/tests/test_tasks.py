import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import TaskColumn

pytestmark = pytest.mark.asyncio


async def get_column_id(db_session: AsyncSession, board_id: int) -> int:
    result = await db_session.execute(
        select(TaskColumn).where(TaskColumn.board_id == board_id).limit(1)
    )
    col = result.scalar_one_or_none()
    return col.id if col else None


async def test_create_task(client: AsyncClient, auth_headers, test_board, db_session):
    col_id = await get_column_id(db_session, test_board.id)
    response = await client.post(
        f"/api/tasks/boards/{test_board.id}/tasks",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "A test task",
            "priority": "high",
            "column_id": col_id,
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["priority"] == "high"


async def test_list_tasks(client: AsyncClient, auth_headers, test_board, db_session):
    col_id = await get_column_id(db_session, test_board.id)
    await client.post(f"/api/tasks/boards/{test_board.id}/tasks", headers=auth_headers,
                      json={"title": "Task 1", "column_id": col_id})
    await client.post(f"/api/tasks/boards/{test_board.id}/tasks", headers=auth_headers,
                      json={"title": "Task 2", "column_id": col_id})

    response = await client.get(f"/api/tasks/boards/{test_board.id}/tasks", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 2


async def test_update_task(client: AsyncClient, auth_headers, test_board, db_session):
    col_id = await get_column_id(db_session, test_board.id)
    create_resp = await client.post(
        f"/api/tasks/boards/{test_board.id}/tasks", headers=auth_headers,
        json={"title": "Original", "column_id": col_id}
    )
    task_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/tasks/{task_id}", headers=auth_headers,
        json={"title": "Updated", "is_completed": True}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated"
    assert update_resp.json()["is_completed"] is True


async def test_move_task(client: AsyncClient, auth_headers, test_board, db_session):
    result = await db_session.execute(
        select(TaskColumn).where(TaskColumn.board_id == test_board.id)
    )
    cols = result.scalars().all()
    assert len(cols) >= 2

    create_resp = await client.post(
        f"/api/tasks/boards/{test_board.id}/tasks", headers=auth_headers,
        json={"title": "Move Me", "column_id": cols[0].id}
    )
    task_id = create_resp.json()["id"]

    move_resp = await client.post(
        f"/api/tasks/{task_id}/move", headers=auth_headers,
        json={"column_id": cols[1].id, "position": 0}
    )
    assert move_resp.status_code == 200
    assert move_resp.json()["column_id"] == cols[1].id


async def test_delete_task(client: AsyncClient, auth_headers, test_board, db_session):
    col_id = await get_column_id(db_session, test_board.id)
    create_resp = await client.post(
        f"/api/tasks/boards/{test_board.id}/tasks", headers=auth_headers,
        json={"title": "Delete Me", "column_id": col_id}
    )
    task_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
    assert del_resp.status_code == 204


async def test_get_task_forbidden(client: AsyncClient, test_board, db_session):
    """Unauthenticated user cannot get tasks."""
    col_id = await get_column_id(db_session, test_board.id)
    response = await client.get(f"/api/tasks/boards/{test_board.id}/tasks")
    assert response.status_code == 401
