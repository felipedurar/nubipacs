
import asyncio
from database.db import init_db
from service_management.services_loader import load_services

async def main():
    # Show Logo
    print(" ===========================================================")
    print(" == NubiPACS - Picture Archiving and Communication System ==")
    print(" == By Felipe Durar                                       ==")
    print(" ===========================================================")

    # Init DB
    init_db()

    # Load the Services
    load_services()

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
