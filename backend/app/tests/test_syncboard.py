"""
SyncBoard Test Suite — 28 tests
Auth×8, Boards×8, Tasks×8, Security×4
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.board import Board, BoardMember, BoardRole
from app.models.task import Task, TaskColumn
from app.core.security import create_access_token, create_refresh_token


# ── Auth (8) ──────────────────────────────────────────────────────────────────

class TestAuth:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json={
            "email": "brand_new@example.com",
            "username": "brandnew",
            "password": "password123",
        })
        assert r.status_code == 201
        assert r.json()["user"]["email"] == "brand_new@example.com"
        assert "hashed_password" not in r.json()["user"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        r = await client.post("/api/auth/register", json={
            "email": test_user.email,
            "username": "different_user",
            "password": "password123",
        })
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        r = await client.post("/api/auth/register", json={
            "email": "another@example.com",
            "username": test_user.username,
            "password": "password123",
        })
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        r = await client.post("/api/auth/register", json={
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "short",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        r = await client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "password123",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        r = await client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "wrongpassword",
        })
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        rt = create_refresh_token({"sub": str(test_user.id)})
        r = await client.post("/api/auth/refresh", json={"refresh_token": rt})
        assert r.status_code == 200
        assert "access_token" in r.json()

    @pytest.mark.asyncio
    async def test_get_me(self, client: AsyncClient, test_user: User, auth_headers: dict):
        r = await client.get("/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == test_user.id


# ── Boards (8) ────────────────────────────────────────────────────────────────

class TestBoards:
    @pytest.mark.asyncio
    async def test_create_board(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/api/boards/", json={
            "name": "My Project Board",
            "color": "#3b82f6",
        }, headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["name"] == "My Project Board"

    @pytest.mark.asyncio
    async def test_list_boards(self, client: AsyncClient, auth_headers: dict, test_board: Board):
        r = await client.get("/api/boards/", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_board(self, client: AsyncClient, auth_headers: dict, test_board: Board):
        r = await client.get(f"/api/boards/{test_board.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == test_board.id

    @pytest.mark.asyncio
    async def test_update_board(self, client: AsyncClient, auth_headers: dict, test_board: Board):
        r = await client.patch(f"/api/boards/{test_board.id}", json={
            "name": "Updated Board Name",
        }, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Updated Board Name"

    @pytest.mark.asyncio
    async def test_other_user_denied(self, client: AsyncClient, auth_headers2: dict, test_board: Board):
        r = await client.get(f"/api/boards/{test_board.id}", headers=auth_headers2)
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_create_column(self, client: AsyncClient, auth_headers: dict, test_board: Board):
        r = await client.post(f"/api/boards/{test_board.id}/columns", json={
            "name": "Backlog",
            "position": 0,
        }, headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["name"] == "Backlog"

    @pytest.mark.asyncio
    async def test_invite_member(
        self, client: AsyncClient, auth_headers: dict,
        test_board: Board, test_user2: User
    ):
        r = await client.post(f"/api/boards/{test_board.id}/members", json={
            "user_id": test_user2.id,
            "role": "member",
        }, headers=auth_headers)
        assert r.status_code == 200  # returns updated board

    @pytest.mark.asyncio
    async def test_delete_board(self, client: AsyncClient, test_user: User):
        token = create_access_token({"sub": str(test_user.id)})
        h = {"Authorization": f"Bearer {token}"}
        created = await client.post("/api/boards/", json={"name": "To Delete"}, headers=h)
        bid = created.json()["id"]
        r = await client.delete(f"/api/boards/{bid}", headers=h)
        assert r.status_code == 204


# ── Tasks (8) ─────────────────────────────────────────────────────────────────

class TestTasks:
    @pytest.mark.asyncio
    async def test_create_task(
        self, client: AsyncClient, auth_headers: dict,
        test_board: Board, test_column: TaskColumn
    ):
        r = await client.post(f"/api/tasks/boards/{test_board.id}/tasks", json={
            "title": "Implement feature",
            "priority": "high",
            "column_id": test_column.id,
        }, headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["title"] == "Implement feature"
        assert r.json()["priority"] == "high"

    @pytest.mark.asyncio
    async def test_get_task(self, client: AsyncClient, auth_headers: dict, test_task: Task):
        r = await client.get(f"/api/tasks/{test_task.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == test_task.id

    @pytest.mark.asyncio
    async def test_list_tasks(
        self, client: AsyncClient, auth_headers: dict,
        test_board: Board, test_task: Task
    ):
        r = await client.get(f"/api/tasks/boards/{test_board.id}/tasks", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    @pytest.mark.asyncio
    async def test_update_task_title(self, client: AsyncClient, auth_headers: dict, test_task: Task):
        r = await client.patch(f"/api/tasks/{test_task.id}", json={
            "title": "Updated Title",
        }, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_task_priority(self, client: AsyncClient, auth_headers: dict, test_task: Task):
        r = await client.patch(f"/api/tasks/{test_task.id}", json={
            "priority": "urgent",
        }, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["priority"] == "urgent"

    @pytest.mark.asyncio
    async def test_move_task(
        self, client: AsyncClient, auth_headers: dict,
        test_board: Board, test_task: Task, db: AsyncSession
    ):
        from sqlalchemy import select
        result = await db.execute(
            select(TaskColumn).where(
                TaskColumn.board_id == test_board.id,
                TaskColumn.id != test_task.column_id,
            ).limit(1)
        )
        other_col = result.scalar_one_or_none()
        if other_col:
            r = await client.post(f"/api/tasks/{test_task.id}/move", json={
                "column_id": other_col.id,
                "position": 0,
            }, headers=auth_headers)
            assert r.status_code == 200
            assert r.json()["column_id"] == other_col.id

    @pytest.mark.asyncio
    async def test_complete_task(self, client: AsyncClient, auth_headers: dict, test_task: Task):
        r = await client.patch(f"/api/tasks/{test_task.id}", json={
            "is_completed": True,
        }, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["is_completed"] is True

    @pytest.mark.asyncio
    async def test_delete_task(
        self, client: AsyncClient, auth_headers: dict,
        test_board: Board, test_column: TaskColumn, test_user: User
    ):
        token = create_access_token({"sub": str(test_user.id)})
        h = {"Authorization": f"Bearer {token}"}
        created = await client.post(f"/api/tasks/boards/{test_board.id}/tasks", json={
            "title": "Delete Me", "column_id": test_column.id,
        }, headers=h)
        tid = created.json()["id"]
        r = await client.delete(f"/api/tasks/{tid}", headers=h)
        assert r.status_code == 204


# ── Security (4) ──────────────────────────────────────────────────────────────

class TestSecurity:
    @pytest.mark.asyncio
    async def test_no_token_rejected(self, client: AsyncClient):
        r = await client.get("/api/boards/")
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, client: AsyncClient):
        r = await client.get("/api/boards/", headers={
            "Authorization": "Bearer totally.invalid.token"
        })
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_task(
        self, client: AsyncClient, test_board: Board,
        test_user2: User, test_column: TaskColumn, db: AsyncSession
    ):
        member = BoardMember(
            board_id=test_board.id,
            user_id=test_user2.id,
            role=BoardRole.VIEWER,
        )
        db.add(member)
        await db.commit()
        token = create_access_token({"sub": str(test_user2.id)})
        r = await client.post(f"/api/tasks/boards/{test_board.id}/tasks", json={
            "title": "Sneak task", "column_id": test_column.id,
        }, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"
