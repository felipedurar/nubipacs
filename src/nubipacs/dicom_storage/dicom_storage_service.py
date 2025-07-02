from nubipacs.dicom_storage.dicom_block_storage.dicom_block_storage import DicomBlockStorage
from nubipacs.dicom_storage.dicom_storage_interface import DicomStorageInterface
from nubipacs.dicom_storage.schemas.dicom_storage_params import DicomStorageParams
from nubipacs.service_management.pacs_service_interface import PACSServiceInterface
from pydantic import ValidationError
from typing import Optional
import threading

class DicomStorageService(PACSServiceInterface):
    def __init__(self, name, type):
        self._thread = None
        self._running = False
        self.name = name
        self.type = type
        self.dicom_storage_params: Optional[DicomStorageParams] = None
        self.dicom_storage: Optional[DicomStorageInterface] = None

    def load_params(self, params):
        # Validate Service Params
        try:
            self.dicom_storage_params = DicomStorageParams(**params)
        except ValidationError as e:
            print(e.json())
            return True

        # Create Storage Type
        match self.dicom_storage_params.target_type:
            case "block-storage":
                self.dicom_storage = DicomBlockStorage()
                self.dicom_storage.load_params(self.dicom_storage_params.params)


    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def restart(self):
        self.stop()
        self.start()

    def _run(self):
        """ Keeping this because in the future i gonna perform runtime checks during service execution... """
        while self._running:
            import time
            time.sleep(10)
