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

class DicomBlockStorage(DicomStorageExtensionInterface):

    def __init__(self):
        self.name: Optional[str] = None
        self.dicom_block_storage_params: Optional[DicomBlockStorageParams] = None

    def load_params(self, params):
        # Validate Service Params
        self.dicom_block_storage_params = params

        # Ensure the output path exists
        os.makedirs(self.dicom_block_storage_params.path, exist_ok=True)

    def save_dicom(self, dataset: Dataset, db_entry):
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


    def find_dicom(self, query: Dataset):
        pass


    def get_dicom(self, sop_instance_uid):
        pass