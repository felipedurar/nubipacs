from nubipacs.service_management.pacs_service_interface import PACSServiceInterface
from nubipacs.dicom.dicom_server import DicomServer
import threading

class DicomService(PACSServiceInterface):
    def __init__(self, name, type):
        self._thread = None
        self._running = False
        self.name = name
        self.type = type
        self.dicom_server = DicomServer()

    def load_params(self, params):
        self.dicom_server.load_params(params)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.dicom_server.stop_server()
        self._running = False

    def restart(self):
        self.stop()
        self.start()

    def _run(self):
        self.dicom_server.initialize_server()
        self.dicom_server.start_server()
