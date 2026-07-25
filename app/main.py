import os
import asyncio
import httpx
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import health, auth, inventory
from app.exceptions.base import PharmacyBaseException
from app.exceptions.handlers import pharmacy_exception_handler

async def ping_render():
    """Background task to ping the Render URL and prevent sleep."""
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        return
    
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(600)  # Ping every 10 minutes
            try:
                await client.get(f"{url}/api/v1/health")
            except Exception:
                pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the keep-alive task in the background
    task = asyncio.create_task(ping_render())
    yield
    # Cleanup on shutdown
    task.cancel()

app = FastAPI(title="Pradhan Pharmacy Automation System", version="1.0.0", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(PharmacyBaseException, pharmacy_exception_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(inventory.router)
from app.api.v1 import agent_inventory
app.include_router(agent_inventory.router)

from app.api.v1 import voice
app.include_router(voice.router)

@app.get("/")

def root():
    return {"message": "Welcome to Pradhan Pharmacy API"}
