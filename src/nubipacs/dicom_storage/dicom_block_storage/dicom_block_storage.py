import os
from typing import Optional

from pydicom import Dataset, dcmread

from nubipacs.dicom_storage.dicom_block_storage.schemas.dicom_block_storage_params import DicomBlockStorageParams
from nubipacs.dicom_storage.dicom_storage_extension_interface import DicomStorageExtensionInterface


class DicomBlockStorage(DicomStorageExtensionInterface):

    def __init__(self):
        self.name: Optional[str] = None
        self.dicom_block_storage_params: Optional[DicomBlockStorageParams] = None

    def load_params(self, params):
        # Validate Service Params
        self.dicom_block_storage_params = params

        # Ensure the output path exists
        os.makedirs(self.dicom_block_storage_params.path, exist_ok=True)

    def build_series_directory_path(self, study_uid, series_uid):
        study_path = os.path.join(self.dicom_block_storage_params.path, study_uid)
        series_path = os.path.join(study_path, series_uid)
        return series_path

    def build_instance_path(self, study_uid, series_uid, instance_uid):
        study_path = os.path.join(self.dicom_block_storage_params.path, study_uid)
        series_path = os.path.join(study_path, series_uid)
        #os.makedirs(series_path, exist_ok=True)
        return os.path.join(series_path, f"{instance_uid}.dcm")

    def save_dicom(self, dataset: Dataset, db_entry):
        # Extract UIDs
        study_uid = dataset.StudyInstanceUID
        series_uid = dataset.SeriesInstanceUID
        instance_uid = dataset.SOPInstanceUID

        # Create Series Path
        series_path = self.build_series_directory_path(study_uid, series_uid)
        os.makedirs(series_path, exist_ok=True)

        # Save file
        filename = self.build_instance_path(study_uid, series_uid, instance_uid)
        dataset.save_as(filename, write_like_original=False)
        print(f"Stored: {filename}")


    def find_dicom(self, query: Dataset):
        pass

    def get_dicom_instance(self, db_entry):
        # Extract UIDs
        study_uid = db_entry['tag_0020000D']
        series_uid = db_entry['tag_0020000E']
        instance_uid = db_entry['tag_00080018']

        # Read Local DCM
        filename = self.build_instance_path(study_uid, series_uid, instance_uid)
        return dcmread(filename, force=True, defer_size="1 KB")


