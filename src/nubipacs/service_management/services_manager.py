from nubipacs.dicom.dicom_service import DicomService
from nubipacs.dicom_storage.dicom_storage_service import DicomStorageService
from nubipacs.service_management.pacs_service_interface import PACSServiceInterface
from nubipacs.utils.singleton_meta import SingletonMeta
from nubipacs.database.models.service import Service
import json, os
from typing import List

class ServicesManager(metaclass=SingletonMeta):
    SERVICES_FILE = "services.json"

    def __init__(self):
        print("Initializing ServicesManager...")
        self.settings = {}
        self.services_config = []
        self.services: List[PACSServiceInterface] = []

    def restore_from_file(self):
        """
        Load the services from the SERVICES_FILE and stores it on MongoDB
        """
        config_file_path = f"./config/{ServicesManager.SERVICES_FILE}"

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

    def load_services_config(self):
        """
        Load the services config from the Mongo DB, if it doesn't exists it tries to load from the SERVICES_FILE
        """
        print("Loading Services Config...")
        self.services_config = Service.objects()
        if len(self.services_config) == 0:
            print("No services found on DB!")
            self.restore_from_file()
        else:
            print("Services Config Loaded Successfully")
            return

        print("Retrieving the Services Config from DB Again")
        self.services_config = Service.objects()

    def initialize_services(self):
        for c_service in self.services_config:
            match c_service.type:
                case "DICOM_SERVER":
                    print(f"Initializing DICOM Service - {c_service.name}")
                    new_dicom_service = DicomService(c_service.name, c_service.type)
                    new_dicom_service.load_params(c_service.params)
                    self.services.append(new_dicom_service)
                case "DCM_STORAGE":
                    print(f"Initializing DCM_STORAGE Service - {c_service.name}")
                    new_storage_service = DicomStorageService(c_service.name, c_service.type)
                    new_storage_service.load_params(c_service.params)
                    self.services.append(new_storage_service)
                case _:
                    print(f"Unknown Service - {c_service.name}")

    def start_services(self):
        for c_service in self.services:
            print(f"Starting Service {c_service.name} (Type: {c_service.type})")
            c_service.start()

    def find_service_by_name(self, name):
        for c_service in self.services:
            if c_service.name == name:
                return c_service
        return None