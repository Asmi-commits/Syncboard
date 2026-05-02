import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "securepass123",
        "full_name": "New User"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["username"] == "newuser"


async def test_register_duplicate_email(client: AsyncClient, test_user):
    response = await client.post("/api/auth/register", json={
        "email": "testuser@example.com",
        "username": "differentuser",
        "password": "securepass123"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


async def test_register_duplicate_username(client: AsyncClient, test_user):
    response = await client.post("/api/auth/register", json={
        "email": "different@example.com",
        "username": "testuser",
        "password": "securepass123"
    })
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"]


async def test_register_weak_password(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "weak@example.com",
        "username": "weakuser",
        "password": "short"
    })
    assert response.status_code == 422


async def test_login_success(client: AsyncClient, test_user):
    response = await client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, test_user):
    response = await client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "anypassword"
    })
    assert response.status_code == 401


async def test_get_me(client: AsyncClient, auth_headers):
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"


async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


async def test_update_me(client: AsyncClient, auth_headers):
    response = await client.patch("/api/auth/me", headers=auth_headers, json={
        "full_name": "Updated Name",
        "avatar_color": "#ff5733"
    })
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


async def test_logout(client: AsyncClient, auth_headers):
    response = await client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 200
