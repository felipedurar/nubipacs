import asyncio
import uvicorn
import threading
from fastapi import FastAPI
from nubipacs.utils.singleton_meta import SingletonMeta

class PacsAPI(metaclass=SingletonMeta):
    SERVICES_FILE = "services.json"

    def __init__(self):
        print("Initializing PacsAPI...")
        self._pacs_api = FastAPI(title="NubiPACS - Picture Archiving and Communication System")
        self._server = None

    async def start_pacs_api(self):
        config = uvicorn.Config(app=self._pacs_api, host="0.0.0.0", port=8005, log_level="info")
        self._server = uvicorn.Server(config)
        await self._server.serve()

    def stop_pacs_api(self):
        if self._server:
            self._server.should_exit = True

    def get_pacs_api(self):
        return self._pacs_api