import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import manager
from app.core.security import decode_token
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.board import Board, BoardMember

router = APIRouter()


async def authenticate_ws(token: str, db: AsyncSession):
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        return None

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()


async def check_ws_board_access(board_id: int, user: User, db: AsyncSession) -> bool:
    result = await db.execute(select(Board).where(Board.id == board_id))
    board = result.scalar_one_or_none()
    if not board:
        return False
    if board.owner_id == user.id:
        return True
    result = await db.execute(
        select(BoardMember).where(BoardMember.board_id == board_id, BoardMember.user_id == user.id)
    )
    return result.scalar_one_or_none() is not None


@router.websocket("/board/{board_id}")
async def board_websocket(
    websocket: WebSocket,
    board_id: int,
    token: str = Query(...),
):
    async with AsyncSessionLocal() as db:
        user = await authenticate_ws(token, db)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return

        has_access = await check_ws_board_access(board_id, user, db)
        if not has_access:
            await websocket.close(code=4003, reason="Forbidden")
            return

    await manager.connect(websocket, board_id, user.id)

    # Notify others user joined
    await manager.broadcast_to_board(board_id, {
        "type": "user_joined",
        "user": {"id": user.id, "username": user.username, "avatar_color": user.avatar_color},
        "active_users": manager.get_board_user_count(board_id),
    }, exclude=websocket)

    try:
        while True:
            data = await websocket.receive_json()

            # Handle ping/pong
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            # Handle cursor position broadcast
            if data.get("type") == "cursor_move":
                await manager.broadcast_to_board(board_id, {
                    "type": "cursor_move",
                    "user_id": user.id,
                    "username": user.username,
                    "position": data.get("position"),
                }, exclude=websocket)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        await manager.broadcast_to_board(board_id, {
            "type": "user_left",
            "user": {"id": user.id, "username": user.username},
            "active_users": manager.get_board_user_count(board_id),
        })
    except Exception as e:
        await manager.disconnect(websocket)
