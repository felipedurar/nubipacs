
from pynetdicom import AE, evt, AllStoragePresentationContexts, VerificationPresentationContexts
from pydicom.dataset import Dataset
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind
import json

debug_logger()

class DicomServer:
    def __init__(self):
        self.server = None
        self.ae = None
        self.handlers = []

    def load_params(self, params):
        self.ae = AE(ae_title=params["ae_title"])
        self.ae.supported_contexts = AllStoragePresentationContexts
        self.ae.add_supported_context(StudyRootQueryRetrieveInformationModelFind)
        self.handlers.append((evt.EVT_REQUESTED, self.handle_association_request))
        self.handlers.append((evt.EVT_ACCEPTED, self.handle_association_accepted))
        self.handlers.append((evt.EVT_C_ECHO, self.handle_echo))
        self.handlers.append((evt.EVT_C_STORE, self.handle_store))
        self.handlers.append((evt.EVT_C_FIND, self.handle_find))

    def handle_association_request(self, event):
        print(" == ASSOCIATION REQUEST ==")
        print(event.assoc.requestor.address)
        print(event.assoc.requested_contexts)

        #print(json.dumps(event.event))
        # calling_aet = event.assoc.requestor.ae_title.strip()
        # print(f"Received association request from: {calling_aet}")
        #
        # allowed_aets = ['WEASIS_AE', 'DEVICE_B']
        #
        # if calling_aet not in allowed_aets:
        #     print(f"Rejecting AE Title: {calling_aet}")
        #     # Return a tuple: (result, source, reason)
        #     # These values are from DICOM PS3.8 Table 9-11
        #     return (0x01, 0x01, 0x03)  # Rejected Permanent, UL Service-user, Calling AE Title not recognized

        # Return None to continue with the association
        return None

    def handle_association_accepted(self, event):
        calling_aet = event.assoc.requestor.ae_title  #.decode().strip()
        print(f"Incoming association from AE Title: {calling_aet}")

        # You can choose to reject based on AE Title
        if calling_aet not in ['WEASIS_AE', 'ALLOWED_AE2']:
            print("Rejecting association from unknown AE Title")
            #event.assoc.release()
            return  # None => association is accepted by default, no return needed
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
        self.server = self.ae.start_server(('0.0.0.0', 11112), block=True, evt_handlers=self.handlers)

    def stop_server(self):
        self.server.shutdown()