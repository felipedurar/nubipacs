import threading

class DicomServerManager:
    def __init__(self):
        self._thread = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self._running:
            print("DICOM server running...")
            import time
            time.sleep(1)

    def stop(self):
        self._running = False

    def restart(self):
        self.stop()
        self.start()