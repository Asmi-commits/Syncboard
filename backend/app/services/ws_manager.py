import json
import asyncio
from typing import Dict, Set, Any
from datetime import datetime
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections per board.
    Supports broadcasting events to all board members with <200ms latency.
    """

    def __init__(self):
        # board_id -> set of (websocket, user_id)
        self.board_connections: Dict[int, Set[tuple]] = {}
        # websocket -> user_id
        self.connection_users: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, board_id: int, user_id: int):
        await websocket.accept()

        if board_id not in self.board_connections:
            self.board_connections[board_id] = set()

        self.board_connections[board_id].add((websocket, user_id))
        self.connection_users[websocket] = user_id

        logger.info(f"User {user_id} connected to board {board_id}")

        # Notify others of new connection
        await self.broadcast(
            board_id=board_id,
            event_type="user_joined",
            data={"user_id": user_id},
            exclude_ws=websocket,
        )

        # Send current online users to the new connection
        online_users = self.get_board_users(board_id)
        await self.send_personal(
            websocket,
            {
                "type": "connection_established",
                "board_id": board_id,
                "online_users": online_users,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def disconnect(self, websocket: WebSocket, board_id: int):
        user_id = self.connection_users.pop(websocket, None)

        if board_id in self.board_connections:
            self.board_connections[board_id].discard((websocket, user_id))
            if not self.board_connections[board_id]:
                del self.board_connections[board_id]

        logger.info(f"User {user_id} disconnected from board {board_id}")
        return user_id

    async def broadcast(
        self,
        board_id: int,
        event_type: str,
        data: Any,
        exclude_ws: WebSocket = None,
        user_id: int = None,
    ):
        if board_id not in self.board_connections:
            return

        message = {
            "type": event_type,
            "board_id": board_id,
            "data": data,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        message_str = json.dumps(message)

        disconnected = set()
        tasks = []

        for ws, uid in self.board_connections[board_id]:
            if ws != exclude_ws:
                tasks.append(self._safe_send(ws, uid, message_str, disconnected))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Cleanup disconnected
        for ws, uid in disconnected:
            self.board_connections[board_id].discard((ws, uid))
            self.connection_users.pop(ws, None)

    async def _safe_send(self, ws: WebSocket, uid: int, message: str, disconnected: set):
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add((ws, uid))

    async def send_personal(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

    def get_board_users(self, board_id: int) -> list:
        if board_id not in self.board_connections:
            return []
        return list({uid for _, uid in self.board_connections[board_id]})

    def get_board_connection_count(self, board_id: int) -> int:
        if board_id not in self.board_connections:
            return 0
        return len(self.board_connections[board_id])

    def get_total_connections(self) -> int:
        return sum(len(conns) for conns in self.board_connections.values())


# Global manager instance
manager = ConnectionManager()
