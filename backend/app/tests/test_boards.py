import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_board(client: AsyncClient, auth_headers):
    response = await client.post("/api/boards/", headers=auth_headers, json={
        "name": "My Board",
        "description": "A test board",
        "color": "#3b82f6"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Board"
    assert data["color"] == "#3b82f6"


async def test_list_boards(client: AsyncClient, auth_headers, test_board):
    response = await client.get("/api/boards/", headers=auth_headers)
    assert response.status_code == 200
    boards = response.json()
    assert len(boards) >= 1
    assert any(b["name"] == "Test Board" for b in boards)


async def test_get_board(client: AsyncClient, auth_headers, test_board):
    response = await client.get(f"/api/boards/{test_board.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == test_board.id


async def test_get_board_not_found(client: AsyncClient, auth_headers):
    response = await client.get("/api/boards/99999", headers=auth_headers)
    assert response.status_code == 404


async def test_update_board(client: AsyncClient, auth_headers, test_board):
    response = await client.patch(
        f"/api/boards/{test_board.id}", headers=auth_headers,
        json={"name": "Updated Board", "color": "#22c55e"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Board"


async def test_delete_board(client: AsyncClient, auth_headers, test_board):
    response = await client.delete(f"/api/boards/{test_board.id}", headers=auth_headers)
    assert response.status_code == 204


async def test_create_board_unauthorized(client: AsyncClient):
    response = await client.post("/api/boards/", json={"name": "Board"})
    assert response.status_code == 401


async def test_invite_member(client: AsyncClient, auth_headers, test_board, test_user2):
    response = await client.post(
        f"/api/boards/{test_board.id}/members", headers=auth_headers,
        json={"user_id": test_user2.id, "role": "member"}
    )
    assert response.status_code == 200
    members = response.json()["members"]
    assert any(m["user"]["id"] == test_user2.id for m in members)
