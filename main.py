import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.websocket import router as websocket_router
from api.routes import router as api_router
from config.settings import Settings
from utils.redis_manager import RedisManager, ConnectionConfig
from contextlib import asynccontextmanager
from config.logging import get_logger

logger = get_logger(__name__)
settings = Settings()

# Initialize Redis manager with configuration
redis_manager = RedisManager()
redis_manager.config = ConnectionConfig(
    host=settings.REDIS_HOST,  # Assuming you have these in your Settings
    port=int(settings.REDIS_PORT),
    retry_interval=5,
    max_retries=3,
    connection_timeout=30,
    heartbeat_interval=30
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Startup: Initialize Redis connection
        await redis_manager.start()
        yield
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        # Shutdown: Clean up resources
        try:
            await redis_manager.stop()
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    description="API with Redis integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(api_router)
app.include_router(websocket_router)

# Add health check endpoint
@app.get("/health")
async def health_check():
    try:
        is_connected = await redis_manager.check_redis_connection()
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "redis_connected": is_connected
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )