from app.database.models.service import Service
import json, os

SERVICES_FILE = "services.json"

_services = []

def restore_from_file():
    config_file_path = f"./config/{SERVICES_FILE}"

    print("Loading Services From Service Json File!")
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as file:
            tmp_services = json.load(file)

            # Save the loaded services on DB
            for c_service in tmp_services:
                service_entity = Service(**c_service)
                service_entity.save()
    else:
        print(f"Config file not found: {config_file_path}")

def load_services():
    global _services
    _services = Service.objects()
    if len(_services) == 0:
        print("No services found on DB!")
        restore_from_file()
    else:
        print(_services)
        return

    print("Retrieving the Services from DB Again")
    _services = Service.objects()
    print(_services)

def list_services():
    return _services
