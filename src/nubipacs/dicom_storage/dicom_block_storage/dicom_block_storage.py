from nubipacs.dicom_storage.dicom_storage_interface import DicomStorageInterface
from nubipacs.dicom_storage.dicom_block_storage.schemas.dicom_block_storage_params import DicomBlockStorageParams
from typing import Optional
from pydantic import ValidationError
from pydicom import Dataset
import os

class DicomBlockStorage(DicomStorageInterface):

    def __init__(self):
        self.dicom_block_storage_params: Optional[DicomBlockStorageParams] = None

    def load_params(self, params):
        # Validate Service Params
        self.dicom_block_storage_params = params
        # try:
        #     self.dicom_block_storage_params = DicomBlockStorageParams(**params)
        # except ValidationError as e:
        #     print(e.json())
        #     return True

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


    def find_dicom(self, query):
        pass

    def get_dicom(self, sop_instance_uid):
        pass