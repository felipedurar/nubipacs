import asyncio
import uvicorn
import threading
from fastapi import FastAPI
from app.utils.singleton_meta import SingletonMeta

class PacsAPI(metaclass=SingletonMeta):
    SERVICES_FILE = "services.json"

    def __init__(self):
        print("Initializing PacsAPI...")
        self.pacs_api = FastAPI()

    async def start_pacs_api(self):
        config = uvicorn.Config(app=self.pacs_api, host="0.0.0.0", port=8005, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    def get_pacs_api(self):
        return self.pacs_api