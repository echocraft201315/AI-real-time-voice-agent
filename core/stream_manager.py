from fastapi.websockets import WebSocket
from config.logging import get_logger
from core.transcriber import DeepgramTranscriber
from core.speech_generator import TextToSpeechHandler
from core.response_generator import ResponseGenerator
from services.websocket_manager import ConnectionManager
from utils.redis_manager import RedisManager 
from utils.queue_manager import QueueManager
import asyncio

logger = get_logger(__name__)

class AudioStreamManager:
    def __init__(self, redis_manager:RedisManager, queue_manager:QueueManager, transcriber:DeepgramTranscriber, manager: ConnectionManager, client_id:str):
        self.redis_manager = redis_manager
        self.queue_manager = queue_manager
        self.transcriber = transcriber
        self.manager = manager
        self.client_id = client_id
        self.tts_generator = TextToSpeechHandler(queue_manager, client_id, provider_name="deepgram")
        self.current_message = None
        self.response_generator = ResponseGenerator(provider="openai", connection_manager=redis_manager)
        # Add cancellation flags
        self.is_running = True
        self._cleanup_event = asyncio.Event()


    async def process_queue(self, client_id: str, websocket: WebSocket):
        """
        Process queue messages with confirmed completion
        If no current message → get new message from queue
        If got message → process it
        If message processed → clear current_message
        If error → clear current_message
        If already has message → wait and continue loop
        """
        try:
            while self.is_running:
                try:
                    # Check for cancellation
                    if self._cleanup_event.is_set():
                        break
                    # Skip getting new message if we're still processing one
                    if self.current_message is None:

                        # If get queue manager take longer than 0.5s, skip
                        try:
                            self.current_message = await asyncio.wait_for(
                                self.queue_manager.get(client_id), 
                                timeout=0.5
                            )
                        except asyncio.TimeoutError:
                            continue

                        # self.current_message = await self.queue_manager.get(client_id)
                        
                        if self.current_message and self.current_message['type'] == 'sentence':
                            logger.info(f"Processing message for {client_id}: {self.current_message['content'][:50]}...")
                            
                            # Stream and wait for completion
                            streaming_success = await self.tts_generator.stream_audio(
                                self.current_message['content'], 
                                websocket
                            )

                            if streaming_success:
                                logger.info(f"Successfully completed message for {client_id}")
                                self.current_message = None
                            else:
                                logger.error(f"Failed to process message for {client_id}, skipping")
                                self.current_message = None  # Skip failed message
                        else:
                            # Not a sentence message or no message
                            self.current_message = None
                            await asyncio.sleep(0.1)
                    else:
                        # We have a message being processed, wait
                        await asyncio.sleep(0.1)

                except RuntimeError as e:
                    if "Cannot call 'send' once a close message has been sent" in str(e):
                        logger.info(f"WebSocket closed for {client_id}")
                        break
                    raise

                except Exception as e:
                    logger.error(f"Queue error for {client_id}: {e}")
                    self.current_message = None  # Clear message on error
                    await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(f"Queue processing cancelled for {client_id}")
        finally:
            self.current_message = None

    async def process_audio(self, client_id: str, websocket: WebSocket):

        try:

            while self.is_running:
                try:
                    # Check for cancellation
                    if self._cleanup_event.is_set():
                        break

                    audio_chunk = await self.manager.receive_audio(websocket)

                    if self.transcriber.transcription_complete and len(self.transcriber.is_finals) > 0:
                        utterance = " ".join(self.transcriber.is_finals)
                        await self.response_generator.process_response(utterance, client_id, websocket)
                        await self.transcriber.reset()

                    if audio_chunk.size > 0:
                        await self.transcriber.transcribe(audio_chunk)

                except Exception as e:
                    await self.transcriber.cleanup()
                    logger.error(f"Audio error for {client_id}: {e}")
                    break
        except asyncio.CancelledError:
            logger.info(f"Audio processing cancelled for {client_id}")
        finally:
            await self.transcriber.cleanup()

    async def cleanup(self):
        """Cleanup resources and stop running tasks"""
        self.is_running = False
        self._cleanup_event.set()
        # Wait for cleanup to complete
        await asyncio.sleep(0.1)