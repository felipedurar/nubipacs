
import asyncio
#import uvicorn
import threading
#from fastapi import FastAPI

async def main():
    # # Start DICOM server in a separate thread
    # dicom_thread = threading.Thread(target=run_dicom_server, daemon=True)
    # dicom_thread.start()
    #
    # # Start background async task
    # asyncio.create_task(periodic_task())
    #
    # # Start FastAPI
    # await start_fastapi()
    pass

if __name__ == "__main__":
    asyncio.run(main())
