
from pynetdicom import AE, evt, AllStoragePresentationContexts, VerificationPresentationContexts
from pydicom.dataset import Dataset
from pynetdicom import AE, debug_logger
from pynetdicom.transport import ThreadedAssociationServer
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind
from pynetdicom.events import Event
from typing import Optional
from pydantic import ValidationError

from app.dicom.schemas.dicom_server_params import DicomServerParams

debug_logger()

class DicomServer:
    def __init__(self):
        self.server: Optional[ThreadedAssociationServer] = None
        self.scp_ae: Optional[AE] = None
        self.handlers = []
        self.dicom_server_params: Optional[DicomServerParams] = None

    def load_params(self, params):
        # Validate Service Params
        try:
            self.dicom_server_params = DicomServerParams(**params)
        except ValidationError as e:
            print(e.json())
            return True

    def initialize_server(self):
        self.scp_ae = AE(ae_title=self.dicom_server_params.ae_title)
        self.scp_ae.supported_contexts = AllStoragePresentationContexts

        # C-ECHO
        #self.scp_ae.add_supported_context(VerificationSOPClass)

        # C-FIND
        self.scp_ae.add_supported_context(StudyRootQueryRetrieveInformationModelFind)

        self.handlers.append((evt.EVT_REQUESTED, self.handle_association_request))
        self.handlers.append((evt.EVT_ACCEPTED, self.handle_association_accepted))
        self.handlers.append((evt.EVT_C_ECHO, self.handle_echo))
        self.handlers.append((evt.EVT_C_STORE, self.handle_store))
        self.handlers.append((evt.EVT_C_FIND, self.handle_find))

    def find_scu_ae_by_ae_title(self, ae_title):
        for c_scu_ae in self.dicom_server_params.aplication_entities:
            if c_scu_ae.ae_title == ae_title:
                return c_scu_ae
        return None

    def handle_association_request(self, event):
        """
        Unfortunatelly pynetdicom doesn't allows us to access the PDU data here
        During the association request it would be the best place to filter IP and AETitles, but it is not possible :/
        """
        return None

    def handle_association_accepted(self, event: Event):
        calling_aet = event.assoc.requestor.ae_title  #.decode().strip()
        print(f"Incoming association from AE Title: {calling_aet}")

        # Find SCU Application Entity
        scu_ae = self.find_scu_ae_by_ae_title(calling_aet)
        if scu_ae is None:
            print(f"No Application Entity Found for Association for AETitle '{calling_aet}'")
            print(f"Rejecting Association for AETitle '{calling_aet}'")
            return event.assoc.abort()

        # Check blocked IPs
        if len(scu_ae.blocked_ips) > 0:
            if event.assoc.requestor.address in scu_ae.blocked_ips:
                print(f"Incoming Association Refused because '{event.assoc.requestor.address}' is on blocked IP list")
                print(f"Rejecting Association for AETitle '{calling_aet}'")
                return event.assoc.abort()

        # Check allowed IPs
        if len(scu_ae.allowed_ips) > 0:
            if event.assoc.requestor.address not in scu_ae.allowed_ips:
                print(f"Incoming Association Refused because '{event.assoc.requestor.address}' is not on allowed IP list")
                print(f"Rejecting Association for AETitle '{calling_aet}'")
                return event.assoc.abort()

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
        dicom_bind_address = str(self.dicom_server_params.bind)
        self.server = self.scp_ae.start_server((dicom_bind_address, self.dicom_server_params.port), block=True, evt_handlers=self.handlers)

    def stop_server(self):
        self.server.shutdown()