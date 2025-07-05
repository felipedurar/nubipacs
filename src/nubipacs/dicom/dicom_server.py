
from pynetdicom import AE, evt, AllStoragePresentationContexts, VerificationPresentationContexts
from pydicom.dataset import Dataset
from pynetdicom import AE, debug_logger, StoragePresentationContexts
from pynetdicom.transport import ThreadedAssociationServer
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind, PatientRootQueryRetrieveInformationModelGet, StudyRootQueryRetrieveInformationModelGet, PatientRootQueryRetrieveInformationModelMove, StudyRootQueryRetrieveInformationModelMove
from pynetdicom.sop_class import CTImageStorage, MRImageStorage, DigitalXRayImageStorageForPresentation
from pynetdicom.events import Event
from typing import Optional
from pydantic import ValidationError
import os, io
from nubipacs.dicom.schemas.dicom_server_params import DicomServerParams
from nubipacs.dicom_storage.dicom_storage_service import DicomStorageService
from typing import Dict

#debug_logger()

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

        # C-GET
        # Add presentation context for C-GET (Query/Retrieve - GET)
        self.scp_ae.add_supported_context(StudyRootQueryRetrieveInformationModelGet)
        self.scp_ae.add_supported_context(PatientRootQueryRetrieveInformationModelGet)
        self.scp_ae.add_requested_context(StudyRootQueryRetrieveInformationModelGet)
        self.scp_ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet)

        self.scp_ae.add_supported_context(StudyRootQueryRetrieveInformationModelMove)
        self.scp_ae.add_supported_context(PatientRootQueryRetrieveInformationModelMove)

        for context in StoragePresentationContexts:
            self.scp_ae.add_supported_context(context.abstract_syntax, ['1.2.840.10008.1.2.1'])
        # for context in StoragePresentationContexts:
        #     self.scp_ae.add_requested_context(context.abstract_syntax, ['1.2.840.10008.1.2.1'])


        # Adiciona todos os Presentation Contexts de armazenamento (necessário para enviar C-STORE)
        for context in AllStoragePresentationContexts:
            self.scp_ae.add_supported_context(context.abstract_syntax, [
                '1.2.840.10008.1.2.1',  # Explicit VR Little Endian
                '1.2.840.10008.1.2'  # Implicit VR Little Endian
            ])
            # self.scp_ae.add_requested_context(context.abstract_syntax, [
            #     '1.2.840.10008.1.2.1',  # Explicit VR Little Endian
            #     '1.2.840.10008.1.2'  # Implicit VR Little Endian
            # ])

        # self.scp_ae.add_requested_context(context.abstract_syntax, [
        #     '1.2.840.10008.1.2.1',  # Explicit VR Little Endian
        #     '1.2.840.10008.1.2'  # Implicit VR Little Endian
        # ])


        self.handlers.append((evt.EVT_REQUESTED, self.handle_association_request))
        self.handlers.append((evt.EVT_ACCEPTED, self.handle_association_accepted))
        self.handlers.append((evt.EVT_C_ECHO, self.handle_echo))
        self.handlers.append((evt.EVT_C_STORE, self.handle_store))
        self.handlers.append((evt.EVT_C_FIND, self.handle_find))
        self.handlers.append((evt.EVT_C_GET, self.handle_get))
        self.handlers.append((evt.EVT_C_MOVE, self.handle_move))
        self.handlers.append((evt.EVT_CONN_CLOSE, self.handle_close))

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

        return

    def handle_echo(self, event):
        print("Received a C-ECHO request")
        return 0x0000  # Success status

    def handle_store(self, event):
        """Handle a C-STORE request event"""
        # Get the dataset from the event
        ds = event.dataset
        ds.file_meta = event.file_meta

        # Get AE Title of the requester
        requestor_ae_title = event.assoc.requestor.ae_title
        print(f"Incoming C-STORE from AE Title: {requestor_ae_title}")

        # Get service and call storage handler
        c_storage_service = self.storage_services[requestor_ae_title]
        c_storage_service.save_dicom(ds)
        return 0x0000

    def handle_find(self, event):
        # Check for cancellation
        if event.is_cancelled:
            yield 0xFE00, None
            return

        # Get AE Title of the requester
        requestor_ae_title = event.assoc.requestor.ae_title
        print(f"Incoming C-STORE from AE Title: {requestor_ae_title}")

        # Get the dataset (the actual query fields)
        ds = event.identifier
        print("C-FIND Query Dataset:")
        print(ds)

        # Extract DICOM tags used in the query
        print("Tags used in query:")
        for elem in ds:
            print(f"{elem.tag} - {elem.name} - {elem.value}")

        # Get service and call storage handler
        c_storage_service = self.storage_services[requestor_ae_title]
        for c_study in c_storage_service.find_dicom(ds):
            yield 0xFF00, c_study

        # Final status
        yield 0x0000, None

    def handle_get(self, event):
        """Generator function to handle a C-GET request."""
        # Check for cancellation
        if event.is_cancelled:
            yield 0xFE00, None
            return

        # Get AE Title of the requester
        requestor_ae_title = event.assoc.requestor.ae_title
        print(f"Incoming C-GET from AE Title: {requestor_ae_title}")

        # Get the dataset (the actual query fields)
        ds = event.identifier
        print("C-GET Query Dataset:")
        print(ds)

        # Extract DICOM tags used in the query
        print("Tags used in query:")
        for elem in ds:
            print(f"{elem.tag} - {elem.name} - {elem.value}")

        # Get service and call storage handler
        c_storage_service = self.storage_services[requestor_ae_title]

        # Perform a Find to count the amount of images
        query_result = list(c_storage_service.find_dicom(ds))
        print(f"GET LEN {len(query_result)}")
        yield len(query_result)

        for c_study in c_storage_service.get_dicom(ds):
            yield 0xFF00, c_study

        # Final status
        yield 0x0000, None

    def handle_move(self, event):
        """Handle C-MOVE request."""
        print("Received C-MOVE request to move destination:", event.move_destination)

        # Check for cancellation
        if event.is_cancelled:
            yield 0xFE00, None
            return

        # Get AE Title of the requester
        requestor_ae_title = event.assoc.requestor.ae_title
        print(f"Incoming C-GET from AE Title: {requestor_ae_title}")

        # Find SCU Application Entity
        scu_ae = self.find_scu_ae_by_ae_title(requestor_ae_title)

        # Get the dataset (the actual query fields)
        ds = event.identifier
        print("C-MOVE Query Dataset:")
        print(ds)

        assoc = event.assoc.ae.associate(
            addr=scu_ae.ip_address,  # IP of move destination AE
            port=scu_ae.port,  # Port of move destination AE
            ae_title=event.move_destination,
            contexts=StoragePresentationContexts
        )

        if assoc.is_established:
            c_storage_service = self.storage_services[requestor_ae_title]

            count = 0
            for c_study in c_storage_service.get_dicom(ds):
                status = assoc.send_c_store(c_study)
                count += 1

            # Release Association created for C-STORE
            assoc.release()

            yield 0x0000, count  # (status, # of completed sub-operations)
        else:
            # Unable to connect to move destination
            yield 0xA801, 0  # Move Destination unknown / cannot connect

    def handle_close(self, event):
        requestor_ae_title = event.assoc.requestor.ae_title
        print(f"Incoming CLOSED CONNECTION from AE Title: {requestor_ae_title}")

    def start_server(self):
        dicom_bind_address = str(self.dicom_server_params.bind)
        self.server = self.scp_ae.start_server((dicom_bind_address, self.dicom_server_params.port), block=True, evt_handlers=self.handlers)

    def stop_server(self):
        self.server.shutdown()