from typing import Optional
from config.logging import get_logger
import json
from utils.redis_manager import RedisManager
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import traceback

class QueueManagerException(Exception):
    """Base exception class for QueueManager"""
    pass

class QueueConnectionError(QueueManagerException):
    """Raised when there are connection issues with Redis"""
    pass

class QueueOperationError(QueueManagerException):
    """Raised when queue operations fail"""
    pass

class QueueManager:
    def __init__(self, redis_manager: RedisManager):
        try:
            if not hasattr(self, 'initialized'):
                if not redis_manager:
                    raise QueueManagerException("Redis manager cannot be None")
                self.redis_client = redis_manager.redis_client
                self.logger = get_logger(__name__)
                self.initialized = True
        except Exception as e:
            self.logger.error(f"Failed to initialize QueueManager: {str(e)}")
            raise QueueManagerException(f"Initialization failed: {str(e)}")

    def get_queue_key(self, user_id: str) -> str:
        """
        Generate queue key for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            str: Queue key
            
        Raises:
            QueueOperationError: If user_id is invalid
        """
        try:
            if not user_id or not isinstance(user_id, str):
                raise QueueOperationError("Invalid user_id")
            return f"queue:{user_id}"
        except Exception as e:
            self.logger.error(f"Error generating queue key: {str(e)}")
            raise QueueOperationError(f"Failed to generate queue key: {str(e)}")

    async def put(self, user_id: str, message: dict) -> None:
        """
        Put a message in the user's queue
        
        Args:
            user_id: User identifier
            message: Message to store
            
        Raises:
            QueueOperationError: If message is invalid or operation fails
            QueueConnectionError: If Redis connection fails
        """
        try:
            if not message or not isinstance(message, dict):
                raise QueueOperationError("Invalid message format")
            
            self.logger.info(f"Adding message to queue for user: {user_id}")
            queue_key = self.get_queue_key(user_id)
            serialized_message = json.dumps(message)
            await self.redis_client.lpush(queue_key, serialized_message)
            
        except ConnectionError as e:
            self.logger.error(f"Redis connection error while putting message: {str(e)}")
            raise QueueConnectionError(f"Connection failed: {str(e)}")
        except (TypeError, json.JSONDecodeError) as e:
            self.logger.error(f"Message serialization error: {str(e)}")
            raise QueueOperationError(f"Message serialization failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in put operation: {str(e)}\n{traceback.format_exc()}")
            raise QueueOperationError(f"Put operation failed: {str(e)}")

    async def get(self, user_id: str, timeout: int = 1) -> Optional[dict]:
        """
        Get a message from the user's queue
        
        Args:
            user_id: User identifier
            timeout: Time to wait for message in seconds
            
        Returns:
            Optional[dict]: Message if available, None otherwise
            
        Raises:
            QueueOperationError: If operation fails
            QueueConnectionError: If Redis connection fails
        """
        try:
            if timeout < 0:
                raise QueueOperationError("Timeout cannot be negative")
                
            queue_key = self.get_queue_key(user_id)
            result = await self.redis_client.brpop(queue_key, timeout=timeout)
            
            if not result:
                return None
                
            return json.loads(result[1])
            
        except ConnectionError as e:
            self.logger.error(f"Redis connection error while getting message: {str(e)}")
            raise QueueConnectionError(f"Connection failed: {str(e)}")
        except TimeoutError as e:
            self.logger.warning(f"Timeout while getting message: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Message deserialization error: {str(e)}")
            raise QueueOperationError(f"Message deserialization failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in get operation: {str(e)}\n{traceback.format_exc()}")
            raise QueueOperationError(f"Get operation failed: {str(e)}")
    
    async def get_length(self, user_id: str) -> int:
        """
        Get the current length of the queue
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Queue length
            
        Raises:
            QueueOperationError: If operation fails
            QueueConnectionError: If Redis connection fails
        """
        try:
            queue_key = self.get_queue_key(user_id)
            return await self.redis_client.llen(queue_key)
            
        except ConnectionError as e:
            self.logger.error(f"Redis connection error while getting queue length: {str(e)}")
            raise QueueConnectionError(f"Connection failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error getting queue length: {str(e)}\n{traceback.format_exc()}")
            raise QueueOperationError(f"Failed to get queue length: {str(e)}")

    async def clear_user_queue(self, user_id: str) -> None:
        """
        Clear all messages from user's queue
        
        Args:
            user_id: User identifier
            
        Raises:
            QueueOperationError: If operation fails
            QueueConnectionError: If Redis connection fails
        """
        try:
            queue_key = self.get_queue_key(user_id)
            await self.redis_client.delete(queue_key)
            self.logger.info(f"Cleared queue for user: {user_id}")
            
        except ConnectionError as e:
            self.logger.error(f"Redis connection error while clearing queue: {str(e)}")
            raise QueueConnectionError(f"Connection failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error clearing user queue: {str(e)}\n{traceback.format_exc()}")
            raise QueueOperationError(f"Failed to clear queue: {str(e)}")