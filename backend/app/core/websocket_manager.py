import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # board_id -> set of WebSocket connections
        self._board_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> user_id
        self._user_map: Dict[WebSocket, int] = {}
        # websocket -> board_id
        self._board_map: Dict[WebSocket, int] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, board_id: int, user_id: int):
        await websocket.accept()
        async with self._lock:
            if board_id not in self._board_connections:
                self._board_connections[board_id] = set()
            self._board_connections[board_id].add(websocket)
            self._user_map[websocket] = user_id
            self._board_map[websocket] = board_id
        logger.info(f"User {user_id} connected to board {board_id}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            board_id = self._board_map.pop(websocket, None)
            user_id = self._user_map.pop(websocket, None)
            if board_id and board_id in self._board_connections:
                self._board_connections[board_id].discard(websocket)
                if not self._board_connections[board_id]:
                    del self._board_connections[board_id]
        logger.info(f"User {user_id} disconnected from board {board_id}")

    async def broadcast_to_board(
        self,
        board_id: int,
        message: dict,
        exclude: Optional[WebSocket] = None,
    ):
        connections = self._board_connections.get(board_id, set()).copy()
        disconnected = []
        for ws in connections:
            if ws == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            await self.disconnect(ws)

    def get_board_user_count(self, board_id: int) -> int:
        return len(self._board_connections.get(board_id, set()))

    def get_active_boards(self) -> list:
        return [
            {"board_id": bid, "users": len(conns)}
            for bid, conns in self._board_connections.items()
        ]


manager = ConnectionManager()
