
from pynetdicom import AE, evt, AllStoragePresentationContexts, VerificationPresentationContexts
from pydicom.dataset import Dataset
from pynetdicom import AE, debug_logger
from pynetdicom.transport import ThreadedAssociationServer
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind
from pynetdicom.sop_class import CTImageStorage, MRImageStorage, DigitalXRayImageStorageForPresentation
from pynetdicom.events import Event
from typing import Optional
from pydantic import ValidationError
import os, io
from nubipacs.dicom.schemas.dicom_server_params import DicomServerParams
from nubipacs.dicom_storage.dicom_storage_service import DicomStorageService
from typing import Dict

debug_logger()

class DicomServer:
    def __init__(self):
        self.server: Optional[ThreadedAssociationServer] = None
        self.scp_ae: Optional[AE] = None
        self.handlers = []
        self.dicom_server_params: Optional[DicomServerParams] = None
        self.storage_services: Dict[str, DicomStorageService] = {}

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

        # C-STORE
        # Add supported presentation contexts
        storage_classes = [
            CTImageStorage,
            MRImageStorage,
            DigitalXRayImageStorageForPresentation
        ]
        for storage_sop in storage_classes:
            self.scp_ae.add_supported_context(storage_sop)

        self.handlers.append((evt.EVT_REQUESTED, self.handle_association_request))
        self.handlers.append((evt.EVT_ACCEPTED, self.handle_association_accepted))
        self.handlers.append((evt.EVT_C_ECHO, self.handle_echo))
        self.handlers.append((evt.EVT_C_STORE, self.handle_store))
        self.handlers.append((evt.EVT_C_FIND, self.handle_find))

        # Lazy Load the Services Manager
        from nubipacs.service_management.services_manager import ServicesManager
        services_manager = ServicesManager()

        # Find the storage service for each application entity
        for c_scu_ae in self.dicom_server_params.aplication_entities:
            self.storage_services[c_scu_ae.ae_title] = services_manager.find_service_by_name(c_scu_ae.storage_service)
            if self.storage_services[c_scu_ae.ae_title] is None:
                print(f"Fatal: Could not find the Storage Service for Application Entity {c_scu_ae.ae_title}")

            storage_service_name = self.storage_services[c_scu_ae.ae_title].name
            print(f" Mapped Storage Service '{storage_service_name}' to RemoteAE '{c_scu_ae.ae_title}' for "
                  f"LocalAE '{self.dicom_server_params.ae_title}'")

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
        """Handle a C-STORE request event"""
        # Get the dataset from the event
        ds = event.dataset
        ds.file_meta = event.file_meta

        requestor_ae_title = event.assoc.requestor.ae_title
        print(f"Incoming C-STORE from AE Title: {requestor_ae_title}")

        c_storage_service = self.storage_services[requestor_ae_title]
        c_storage_service.dicom_storage.save_dicom(ds)

        # # Extract UIDs
        # study_uid = ds.StudyInstanceUID
        # series_uid = ds.SeriesInstanceUID
        # instance_uid = ds.SOPInstanceUID
        #
        # # Create directory structure
        # study_path = os.path.join(OUTPUT_DIR, study_uid)
        # series_path = os.path.join(study_path, series_uid)
        # os.makedirs(series_path, exist_ok=True)
        #
        # # Save file
        # filename = os.path.join(series_path, f"{instance_uid}.dcm")
        # ds.save_as(filename, write_like_original=False)
        #
        # print(f"Stored: {filename}")

        # Return a 'Success' status
        return 0x0000

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