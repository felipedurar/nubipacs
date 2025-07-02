from nubipacs.dicom_storage.dicom_storage_interface import DicomStorageInterface
from nubipacs.dicom_storage.dicom_block_storage.schemas.dicom_block_storage_params import DicomBlockStorageParams
from typing import Optional
from pydantic import ValidationError
from pydicom import Dataset, DataElement
from pydicom.tag import Tag
from mongoengine.context_managers import switch_db
import os

from nubipacs.dicom_storage.models.dcm_instance import DcmInstance


class DicomBlockStorage(DicomStorageInterface):

    def __init__(self):
        self.name: Optional[str] = None
        self.dicom_block_storage_params: Optional[DicomBlockStorageParams] = None

    def load_params(self, name, params):
        # Validate Service Params
        self.name = name
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

        # Store Metadata on Database
        with switch_db(DcmInstance, self.name) as DcmInstanceDB:
            c_instance = DcmInstanceDB()
            for elem in dataset:
                element_pair = self.filter_dicom_tag(elem)
                #c_instance[element_pair[0]] = element_pair[1]
            #c_instance.save()

    def filter_dicom_tag(self, elem: DataElement):
        tag_hex = f"{elem.tag.group:04X}{elem.tag.element:04X}"
        if elem.VR == 'OB' or elem.VR == 'OW' or elem.VR == 'OF' or elem.VR == 'UN' or elem.tag == Tag(0x7FE0,
                                                                                                       0x0010):  # PixelData
            print(f"{elem.tag} {tag_hex} {elem.name} = <binary data skipped>")
            return (tag_hex, '<binary data skipped>')
        else:
            print(f"{elem.tag} {tag_hex} {elem.name} = {elem.value}")
            return (tag_hex, elem.value)


    def find_dicom(self, query):
        pass

    def get_dicom(self, sop_instance_uid):
        pass