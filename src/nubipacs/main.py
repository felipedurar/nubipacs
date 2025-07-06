# ===========================================================
# NubiPACS - Picture Archiving and Communication System
# Coded By Felipe Durar
# ===========================================================

print(" ===========================================================")
print(" == NubiPACS - Picture Archiving and Communication System ==")
print(" == By Felipe Durar                                       ==")
print(" ===========================================================")

from nubipacs.service_management.services_manager import ServicesManager
from database.db import init_db
from nubipacs.pacs_api.pacs_api import PacsAPI
import asyncio

services_manager = ServicesManager()
pacs_api = PacsAPI()

async def main():
    # Init DB
    init_db()

    # Load and start the Services
    services_manager.load_services_config()
    services_manager.initialize_services()
    await services_manager.start_services()

    await pacs_api.start_pacs_api()


if __name__ == "__main__":
    asyncio.run(main())
