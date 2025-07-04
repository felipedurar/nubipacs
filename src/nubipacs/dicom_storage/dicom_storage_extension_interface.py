from abc import ABC, abstractmethod

from nubipacs.dicom_storage.models.dcm_instance import DcmInstance
from pydicom import Dataset

class DicomStorageExtensionInterface(ABC):
    @abstractmethod
    def load_params(self, params):
        pass

    @abstractmethod
    def save_dicom(self, dataset: Dataset, db_entry):
        pass

    @abstractmethod
    def find_dicom(self, query: Dataset):
        pass

    @abstractmethod
    def get_dicom_instance(self, db_entry):
        pass
