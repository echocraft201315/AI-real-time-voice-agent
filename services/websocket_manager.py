from fastapi import WebSocket
from typing import List
import numpy as np
from config.logging import logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(message)
        
    async def receive_audio(self, websocket: WebSocket) -> np.ndarray:
        try:
            data = await websocket.receive_bytes()
            audio_array = np.frombuffer(data, dtype=np.uint8)
            logger.info(f"Received audio chunk of size: {len(audio_array)}")
            return audio_array
        except Exception as e:
            logger.error(f"Error receiving audio: {e}")
            raise