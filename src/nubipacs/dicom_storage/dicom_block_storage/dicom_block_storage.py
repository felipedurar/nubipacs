from nubipacs.dicom_storage.dicom_storage_extension_interface import DicomStorageExtensionInterface
from nubipacs.dicom_storage.dicom_storage_interface import DicomStorageInterface
from nubipacs.dicom_storage.dicom_block_storage.schemas.dicom_block_storage_params import DicomBlockStorageParams
from typing import Optional, Any
from pydantic import ValidationError
from pydicom import Dataset, DataElement
from pydicom.tag import Tag, BaseTag
from pydicom.multival import MultiValue
from pydicom.valuerep import PersonName, VR
from pydicom.datadict import dictionary_VR
from mongoengine.context_managers import switch_db
from mongoengine import NotUniqueError
from pymongo.errors import DuplicateKeyError
import os

from nubipacs.dicom_storage.models.dcm_instance import DcmInstance

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

class DicomBlockStorage(DicomStorageExtensionInterface):

    def __init__(self):
        self.name: Optional[str] = None
        self.dicom_block_storage_params: Optional[DicomBlockStorageParams] = None

    def load_params(self, name, params):
        # Validate Service Params
        self.name = name
        self.dicom_block_storage_params = params

        # Ensure the output path exists
        os.makedirs(self.dicom_block_storage_params.path, exist_ok=True)

    def save_dicom(self, dataset: Dataset):
        # Extract UIDs
        study_uid = dataset.StudyInstanceUID
        series_uid = dataset.SeriesInstanceUID
        instance_uid = dataset.SOPInstanceUID

        # Create directory structure
        study_path = os.path.join(self.dicom_block_storage_params.path, study_uid)
        series_path = os.path.join(study_path, series_uid)
        os.makedirs(series_path, exist_ok=True)

        # Save file
        filename = os.path.join(series_path, f"{instance_uid}.dcm")
        dataset.save_as(filename, write_like_original=False)
        print(f"Stored: {filename}")

        # Store Metadata on Database
        with switch_db(DcmInstance, self.name) as DcmInstanceDB:
            c_inst_dict = {}
            for elem in dataset:
                hex_tag = self.get_hex_tag(elem.tag)
                element_val = '<binary data skipped>' if self.is_binary_element(elem) else self.prepare_dcm_element_val(elem.value)
                if hex_tag in instance_metadata_tags:
                    document_key = f"tag_{hex_tag}"
                    c_inst_dict[document_key] = element_val

            # It creates or update if already exists
            DcmInstanceDB.objects(tag_00080018=c_inst_dict['tag_00080018']).update_one(
                **c_inst_dict,
                upsert=True
            )


    def prepare_dcm_element_val(self, elem: Any):
        if isinstance(elem, MultiValue):
            return list(elem)
        elif isinstance(elem, PersonName):
            return str(elem)
        else:
            return elem

    def get_hex_tag(self, tag: Tag):
        return f"{tag.group:04X}{tag.element:04X}"

    def is_binary_element(self, elem: DataElement):
        return elem.VR == 'OB' or elem.VR == 'OW' or elem.VR == 'OF' or elem.VR == 'UN' or elem.tag == Tag(0x7FE0,
                                                                                                       0x0010)  # PixelData

    def find_dicom(self, query: Dataset):
        # Extract DICOM tags used in the query
        print("Tags used in query:")
        for elem in query:
            print(f"{elem.tag} - {elem.name} - {elem.value}")

        query_retrieve_level = query.get((0x0008, 0x0052), None)

        filters = {}
        for elem in query:
            print(f"{elem.tag} - {elem.name} - {elem.value}")
            hex_tag = self.get_hex_tag(elem.tag)
            if self.get_hex_tag(elem.tag) in instance_metadata_tags and elem.value is not None:
                prepared_value = self.prepare_dcm_element_val(elem.value)
                if isinstance(prepared_value, str) and not prepared_value:
                    continue

                document_key = f"tag_{hex_tag}"
                filters[document_key] = prepared_value
        print("FILTERS")
        print(filters)

        with switch_db(DcmInstance, self.name) as DcmInstanceDB:
            studies_found = DcmInstanceDB.objects(**filters).limit(1000)

            for c_study in studies_found:
                c_study_dataset = Dataset()
                data = c_study.to_mongo().to_dict()
                for field, value in data.items():
                    if not field.startswith('tag_'):
                        continue

                    tag_str = str(field).split('_')[1]
                    c_tag = Tag(int(tag_str, 16))
                    vr = dictionary_VR(c_tag)
                    c_study_dataset.add_new(c_tag,vr, value)
                    #c_study_dataset.add()

                yield c_study_dataset


    def get_dicom(self, sop_instance_uid):
        pass