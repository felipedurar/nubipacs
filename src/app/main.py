# ===========================================================
# NubiPACS - Picture Archiving and Communication System
# Coded By Felipe Durar
# ===========================================================

print(" ===========================================================")
print(" == NubiPACS - Picture Archiving and Communication System ==")
print(" == By Felipe Durar                                       ==")
print(" ===========================================================")

import asyncio

from app.service_management.services_manager import ServicesManager
from database.db import init_db

services_manager = ServicesManager()

async def main():
    # Init DB
    init_db()

    # Load and start the Services
    services_manager.load_services_config()
    services_manager.initialize_services()
    services_manager.start_services()

    # Block the Thread
    while len(services_manager.services) > 0:
        await asyncio.sleep(10)

    # # Start DICOM server in a separate thread
    # dicom_thread = threading.Thread(target=run_dicom_server, daemon=True)
    # dicom_thread.start()
    #
    # # Start background async task
    # asyncio.create_task(periodic_task())
    #
    # # Start FastAPI
    # await start_fastapi()
    #pass

if __name__ == "__main__":
    asyncio.run(main())
