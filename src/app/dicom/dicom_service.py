from app.service_management.pacs_service import PACSService
from dicom_server import DicomServer
import threading

class DicomService(PACSService):
    def __init__(self, params):
        self._thread = None
        self._running = False
        self.dicom_server = DicomServer()
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
        self.dicom_server.start_server()
