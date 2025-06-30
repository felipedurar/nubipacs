
from pynetdicom import AE, evt, AllStoragePresentationContexts, VerificationPresentationContexts
from pydicom.dataset import Dataset

class DicomServer:
    def __init__(self):
        self.ae = None
        self.handlers = []

    def load_params(self, params):
        self.ae = AE(ae_title=params.ae_title)
        self.ae.supported_contexts = AllStoragePresentationContexts
        self.handlers.append((evt.EVT_ACCEPTED, self.handle_association_request))
        self.handlers.append((evt.EVT_C_ECHO, self.handle_echo))
        self.handlers.append((evt.EVT_C_STORE, self.handle_store))
        self.handlers.append((evt.EVT_C_FIND, self.handle_find))

    def handle_association_request(self, event):
        calling_aet = event.assoc.requestor.ae_title.decode().strip()
        print(f"Incoming association from AE Title: {calling_aet}")

        # You can choose to reject based on AE Title
        if calling_aet not in ['ALLOWED_AE1', 'ALLOWED_AE2']:
            print("Rejecting association from unknown AE Title")
            return  # None → association is accepted by default, no return needed
        return

    def handle_echo(self, event):
        print("Received a C-ECHO request")
        return 0x0000  # Success status

    def handle_store(self, event):
        ds = event.dataset
        ds.file_meta = event.file_meta

        # Save the dataset to file
        ds.save_as(f"{ds.SOPInstanceUID}.dcm", write_like_original=False)
        print(f"Stored DICOM file: {ds.SOPInstanceUID}.dcm")

        return 0x0000  # Success

    def handle_find(self, event):
        ds = event.identifier
        print(f"Received C-FIND request: {ds}")

        # Example response dataset
        rsp = Dataset()
        rsp.PatientName = 'DOE^JOHN'
        rsp.PatientID = '123456'
        rsp.StudyInstanceUID = '1.2.3.4.5'
        rsp.QueryRetrieveLevel = 'PATIENT'

        # Yield one or more matches
        yield (0xFF00, rsp)  # Pending

        # Signal completion
        yield (0x0000, None)  # Success

    def start_server(self):
        self.ae.start_server(('0.0.0.0', 11112), block=True, evt_handlers=self.handlers)