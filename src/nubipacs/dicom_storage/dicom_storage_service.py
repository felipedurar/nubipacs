from nubipacs.dicom_storage.dicom_block_storage.dicom_block_storage import DicomBlockStorage
from nubipacs.dicom_storage.dicom_storage_change_service import DicomStorageChangeService
from nubipacs.dicom_storage.dicom_storage_extension_interface import DicomStorageExtensionInterface
from nubipacs.dicom_storage.dicom_storage_interface import DicomStorageInterface
from nubipacs.dicom_storage.models.dcm_change import DcmChange
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
from datetime import datetime, timedelta
import asyncio
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
dicom_storage_change_service = DicomStorageChangeService()

class DicomStorageService(PACSServiceInterface, DicomStorageInterface):

    def __init__(self, name, type):
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


    async def start(self):
        if self._running:
            return
        self._running = True
        asyncio.create_task(self.sync_dcm_changes())
        asyncio.create_task(self.process_dcm_changes())

    def stop(self):
        self._running = False

    def restart(self):
        self.stop()
        self.start()

    async def sync_dcm_changes(self):
        while self._running:
            with switch_db(DcmChange, self.name) as DcmChangeDB:
                change_list_db =  DcmChangeDB.objects()
                change_list_local = dicom_storage_change_service.get_change_list()

                # Synchronize Local Change List with the DB Change List
                # Basically checks if the DB Change reports are older than the local ones, case it is older just update the change_datetime
                for c_local_change in change_list_local:
                    print(f"Local: {c_local_change}")
                    change_report_found = next((x for x in change_list_db if x.study_instance_uid == c_local_change['study_instance_uid']), None)
                    if change_report_found is None:
                        # The Current Change Report doesn't exists on DB...
                        change_report_found = DcmChangeDB()
                        change_report_found.study_instance_uid = c_local_change['study_instance_uid']
                        change_report_found.change_datetime = c_local_change['change_datetime']
                        change_report_found.execution_started = False
                        change_report_found.execution_started_datetime = None
                        change_report_found.save()
                    elif c_local_change['change_datetime'] > change_report_found.change_datetime:
                        change_report_found.change_datetime = c_local_change['change_datetime']
                        change_report_found.save()
                # Clear List
                dicom_storage_change_service.clear_change_list()

            await asyncio.sleep(2)

    async def process_dcm_changes(self):
        while self._running:
            with switch_db(DcmChange, self.name) as DcmChangeDB:
                # Process the pending studies that reached the timeout
                change_list_db = DcmChangeDB.objects.filter(**{ 'execution_started': False })
                for c_db_change in change_list_db:
                    c_db_change_dict = c_db_change.to_mongo().to_dict()
                    print(f"DB: {c_db_change_dict}")

                    if datetime.now() - c_db_change.change_datetime > timedelta(seconds=10):
                        print(f" - Study '{c_db_change.study_instance_uid}' metadata processing triggered by change report timeout!")
                        asyncio.create_task(self.process_study(c_db_change.id))

            await asyncio.sleep(2)

    async def process_study(self, doc_id):
        #print(f" ## PROCESSING STUDY {study_instance_uid}")

        with switch_db(DcmChange, self.name) as DcmChangeDB:
            # Process the pending studies that reached the timeout
            change_report = DcmChangeDB.objects.get(id=doc_id)
            if change_report is None:
                print(f"Error retrieving study change report {str(doc_id)}")
                return

            print(f" ## PROCESSING STUDY '{change_report.study_instance_uid}'")
            change_report.execution_started = True
            change_report.execution_started_datetime = datetime.now()
            change_report.save()

            # PERFORM THE PROCESSING HERE!!
            await asyncio.sleep(2)

            print(f" ## PROCESSING STUDY FINISHED '{change_report.study_instance_uid}'")

            # Now that it was processed, delete it
            change_report.delete()

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

            # Report Used
            dicom_storage_change_service.report_study_changed(dataset.StudyInstanceUID)

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
