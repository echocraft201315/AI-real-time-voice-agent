from fastapi import APIRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect
from services.websocket_manager import ConnectionManager
from config.logging import get_logger
from config.settings import Settings
# from utils.save_audio import AudioSaver
from core.transcriber import DeepgramTranscriber
from core.stream_manager import AudioStreamManager
from utils.redis_manager import RedisManager 
from utils.queue_manager import QueueManager
import asyncio
from typing import Optional

logger = get_logger(__name__)
router = APIRouter()
manager = ConnectionManager()
# audio_saver = AudioSaver()
setting = Settings()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        data = await websocket.receive_text()
        await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in text websocket: {e}")
    finally:
        await manager.disconnect(websocket)


@router.websocket("/ws/audio/{client_id}")
async def audio_websocket_endpoint(websocket: WebSocket, client_id: str):
    # Get Redis manager from application state
    redis_manager = RedisManager()
    queue_manager = QueueManager(redis_manager)
    transcriber = DeepgramTranscriber(setting.DEEPGRAM_API_KEY, websocket)
    stream_manager = AudioStreamManager(redis_manager, queue_manager, transcriber, manager, client_id)
    tasks: list[asyncio.Task] = []
    
    async def cancel_tasks():
        """Helper function to cancel tasks properly"""
        if tasks:
            # Cancel all tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for all tasks to complete their cancellation
            await asyncio.gather(*tasks, return_exceptions=True)
            tasks.clear()

    try:
        await manager.connect(websocket)
        await transcriber.initialize()

        # Create tasks with names for better debugging
        queue_task = asyncio.create_task(
            stream_manager.process_queue(client_id, websocket),
            name=f"queue_task_{client_id}"
        )
        audio_task = asyncio.create_task(
            stream_manager.process_audio(client_id, websocket),
            name=f"audio_task_{client_id}"
        )
        tasks.extend([queue_task, audio_task])

        # Wait for any task to complete or fail
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )

        # If we get here, one of the tasks completed or failed
        for task in done:
            if task.exception():
                raise task.exception()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {client_id}")
        
    except Exception as e:
        logger.error(f"Error in audio websocket: {str(e)}")
        # Optionally send error message to client
        try:
            await websocket.send_json({
                "type": "error",
                "message": "An error occurred in the connection"
            })
        except:
            pass
        raise  # Re-raise the exception after cleanup

    finally:
        # Comprehensive cleanup in specific order
        try:
            # 1. Cancel ongoing tasks
            await cancel_tasks()
            
            # 2. Cleanup stream manager
            await stream_manager.cleanup()
            
            # 3. Cleanup transcriber
            await transcriber.cleanup()
            
            # 4. Clear queue
            await queue_manager.clear_user_queue(client_id)
            
            # 5. Disconnect from WebSocket
            await manager.disconnect(websocket)
            
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup for {client_id}: {str(cleanup_error)}")

