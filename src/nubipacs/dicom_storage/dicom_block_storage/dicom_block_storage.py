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

store_metadata_dicom_tags = [
    "00100020", "00100010", "00100030", "00100040",
    "0020000D", "00080020", "00080030", "00080050",
    "00200010", "00081030", "00080090", "00080061",
    "00201000", "00201002", "0020000E", "00200011",
    "0008103E", "00080060", "00180015", "00200060",
    "00201209", "00080021", "00080018", "00200013",
    "00080008", "00080022", "00080023", "00280010",
    "00280100", "00280004", "00280030"
]

class DicomBlockStorage(DicomStorageInterface):

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
            c_instance = DcmInstanceDB()
            for elem in dataset:
                hex_tag = self.get_hex_tag(elem.tag)
                element_val = '<binary data skipped>' if self.is_binary_element(elem) else self.prepare_dcm_element_val(elem)
                if hex_tag in store_metadata_dicom_tags:
                    document_key = f"tag_{hex_tag}"
                    c_instance[document_key] = self.prepare_dcm_element_val(element_val)
            try:
                print(c_instance)
                c_instance.save()
            except NotUniqueError as e:
                # TODO: SHOULD UPDATE THE EXISTING ITEM!!
                print("Duplicate detected:", e)
            except DuplicateKeyError as e:
                # TODO: SHOULD UPDATE THE EXISTING ITEM!!
                print("Duplicate detected:", e)

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
        if elem.VR == 'OB' or elem.VR == 'OW' or elem.VR == 'OF' or elem.VR == 'UN' or elem.tag == Tag(0x7FE0,
                                                                                                       0x0010):  # PixelData
            return True
        return False

    def find_dicom(self, query: Dataset):
        # Extract DICOM tags used in the query
        print("Tags used in query:")
        for elem in query:
            print(f"{elem.tag} - {elem.name} - {elem.value}")

        filters = {}
        for elem in query:
            print(f"{elem.tag} - {elem.name} - {elem.value}")
            hex_tag = self.get_hex_tag(elem.tag)
            if elem.value is not None:
                document_key = f"tag_{hex_tag}"
                filters[document_key] = elem.value

        with switch_db(DcmInstance, self.name) as DcmInstanceDB:
            studies_found = DcmInstanceDB.objects(**filters).limit(1000)

            for c_study in studies_found:
                c_study_dataset = Dataset()
                data = c_study.to_mongo().to_dict()
                for field, value in data.items():
                    #print(f"{field}: {value}")
                    tag_str = str(field).split('_')[1]
                    c_tag = Tag(int(tag_str, 16))
                    vr = dictionary_VR(c_tag)
                    c_study_dataset.add_new(c_tag,vr, value)
                    #c_study_dataset.add()

                # match.add
                # match.PatientName = 'DOE^JOHN'
                # match.PatientID = '123456'
                # match.StudyInstanceUID = '1.2.3.4.5.6'
                # match.StudyDate = '20250101'
                yield c_study_dataset


    def get_dicom(self, sop_instance_uid):
        pass