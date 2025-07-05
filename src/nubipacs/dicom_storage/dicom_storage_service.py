from nubipacs.dicom_storage.dicom_block_storage.dicom_block_storage import DicomBlockStorage
from nubipacs.dicom_storage.dicom_storage_extension_interface import DicomStorageExtensionInterface
from nubipacs.dicom_storage.dicom_storage_interface import DicomStorageInterface
from nubipacs.dicom_storage.models.dcm_instance import DcmInstance
from nubipacs.dicom_storage.schemas.dicom_storage_params import DicomStorageParams
from nubipacs.service_management.pacs_service_interface import PACSServiceInterface
from pydicom.multival import MultiValue
from pydicom.valuerep import PersonName, VR
from pydicom import Dataset, DataElement
from pydicom.tag import Tag, BaseTag
from pydicom.datadict import dictionary_VR
from mongoengine.context_managers import switch_db
from mongoengine import connect, register_connection
from pydantic import ValidationError
from typing import Optional, Any
import threading

patient_level_tags = [
    "00100020", "00100010", "00100030", "00100040"
]

study_level_tags = [
    "0020000D", "00080020", "00080030", "00080050",
    "00200010", "00081030", "00080090", "00080061",
    "00201000", "00201002"
]

series_level_tags = [
    "0020000E", "00200011", "0008103E", "00080060",
    "00180015", "00200060", "00201209", "00080021",
    "00080031"
]

instance_level_tags = [
    "00080018", "00200013", "00080008", "00080022",
    "00080032", "00080023", "00080033", "00280010",
    "00280100", "00280004", "00280030"
]

study_metadata_tags = [
    *study_level_tags,
    *patient_level_tags
],

series_metadata_tags = [
    *study_level_tags,
    *patient_level_tags,
    *series_level_tags
]

instance_metadata_tags = [
    *patient_level_tags,
    *study_level_tags,
    *series_level_tags,
    *instance_level_tags
]

DB_TAG_FIELD_PREFIX = "tag_"

class DicomStorageService(PACSServiceInterface, DicomStorageInterface):

    def __init__(self, name, type):
        self._thread = None
        self._running = False
        self.name = name
        self.type = type
        self.dicom_storage_params: Optional[DicomStorageParams] = None
        self.dicom_storage_extension: Optional[DicomStorageExtensionInterface] = None

    def load_params(self, params):
        # Validate Service Params
        try:
            self.dicom_storage_params = DicomStorageParams(**params)
        except ValidationError as e:
            print(e.json())
            return True

        # Start Dataase connection
        register_connection(
            alias=self.name,
            name=self.name,
            host=self.dicom_storage_params.metadata_db
        )

        # Create Storage Type
        match self.dicom_storage_params.target_type:
            case "block-storage":
                self.dicom_storage_extension = DicomBlockStorage()
                self.dicom_storage_extension.load_params(self.dicom_storage_params.params)


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
        """ Keeping this because in the future I'm going to perform runtime checks during service execution... """
        while self._running:
            import time
            time.sleep(10)

    def prepare_dcm_element_val(self, elem: Any):
        """ Prepares the value of a DCM Element to be stored into the Database as a Value """
        if isinstance(elem, MultiValue):
            return list(elem)
        elif isinstance(elem, PersonName):
            return str(elem)
        else:
            return elem

    def get_hex_tag(self, tag: Tag):
        return f"{tag.group:04X}{tag.element:04X}"

    def get_db_field_name(self, hex_tag: str):
        return f"{DB_TAG_FIELD_PREFIX}{hex_tag}"

    def is_binary_element(self, elem: DataElement):
        return elem.VR == 'OB' or elem.VR == 'OW' or elem.VR == 'OF' or elem.VR == 'UN' or elem.tag == Tag(0x7FE0,
                                                                                                       0x0010)  # PixelData

    def save_dicom(self, dataset: Dataset):
        # Store Metadata on Database
        with switch_db(DcmInstance, self.name) as DcmInstanceDB:
            # Create the instance DB entry (a dictionary)
            instance_db_enty = {'dataset': {}, 'sop_instance_uid': dataset.SOPInstanceUID,
                                'series_instance_uid': dataset.SeriesInstanceUID,
                                'study_instance_uid': dataset.StudyInstanceUID}

            for elem in dataset:
                # Generate the TAG (XXXXXXXX) and prepares the value to be added/updated to the DB
                hex_tag = self.get_hex_tag(elem.tag)
                element_val = '[BINARY]' if self.is_binary_element(elem) else self.prepare_dcm_element_val(elem.value)

                # Check if the Tag is in the list of Tags that are going to be stored on DB
                if hex_tag in instance_metadata_tags:
                    document_key = self.get_db_field_name(hex_tag)
                    instance_db_enty['dataset'][document_key] = element_val

            # Call the extension
            # Pass the c_inst_dict (DB Entry) in case the extension need to save anything on the DB
            self.dicom_storage_extension.save_dicom(dataset, instance_db_enty)

            # It creates or update if already exists
            # tag_00080018 = SOP Instance UID (Unique Instance ID)
            DcmInstanceDB.objects(sop_instance_uid=dataset.SOPInstanceUID).update_one(
                **instance_db_enty,
                upsert=True
            )

    def find_dicom(self, query: Dataset):
        # Get Query Retrieve Level
        # WARNING: probably the query_retrieve_level will not come as a str
        query_retrieve_level = query.get((0x0008, 0x0052), None)
        if query_retrieve_level in [None, '']:
            query_retrieve_level = 'STUDY'

        # Build Mongo Query based on C-FIND DataSet
        filters = {}
        for elem in query:
            # Filter only Elements that are on the Instance Metadata List (The elements that are )
            hex_tag = self.get_hex_tag(elem.tag)
            if hex_tag in instance_metadata_tags and elem.value is not None:
                prepared_value = self.prepare_dcm_element_val(elem.value)

                # Ignore if it is an empty value
                if isinstance(prepared_value, str) and not prepared_value:
                    continue

                document_key = self.get_db_field_name(hex_tag)
                filters[f"dataset__{document_key}"] = prepared_value

        with switch_db(DcmInstance, self.name) as DcmInstanceDB:
            studies_found = DcmInstanceDB.objects.filter(**filters).limit(1000)

            for c_study in studies_found:
                # TODO: Handle Cancellation HERE!
                c_study_dataset = Dataset()
                db_entry_dataset = c_study.to_mongo().to_dict()['dataset']
                for field, value in db_entry_dataset.items():
                    if not field.startswith(DB_TAG_FIELD_PREFIX):
                        continue

                    tag_str = str(field).split('_')[1]
                    c_tag = Tag(int(tag_str, 16))
                    vr = dictionary_VR(c_tag)
                    c_study_dataset.add_new(c_tag,vr, value)

                yield c_study_dataset

    def get_dicom(self, query: Dataset):
        # Get Query Retrieve Level
        # WARNING: probably the query_retrieve_level will not come as a str
        query_retrieve_level = query.get((0x0008, 0x0052), None)
        if query_retrieve_level in [None, '']:
            query_retrieve_level = 'STUDY'

        # Build Mongo Query based on C-FIND DataSet
        filters = {}
        for elem in query:
            # Filter only Elements that are on the Instance Metadata List (The elements that are )
            hex_tag = self.get_hex_tag(elem.tag)
            if hex_tag in instance_metadata_tags and elem.value is not None:
                prepared_value = self.prepare_dcm_element_val(elem.value)

                # Ignore if it is an empty value
                if isinstance(prepared_value, str) and not prepared_value:
                    continue

                document_key = self.get_db_field_name(hex_tag)
                filters[f"dataset__{document_key}"] = prepared_value

        with switch_db(DcmInstance, self.name) as DcmInstanceDB:
            studies_found = DcmInstanceDB.objects.filter(**filters).limit(1000)

            for c_study in studies_found:
                # TODO: Handle Cancellation HERE!
                c_study_dataset = Dataset()
                db_entry_dataset = c_study.to_mongo().to_dict()['dataset']

                yield self.dicom_storage_extension.get_dicom_instance(db_entry_dataset)
