from abc import ABC, abstractmethod
from pydicom import Dataset

class DicomStorageInterface(ABC):

    @abstractmethod
    def load_params(self, params):
        pass

    @abstractmethod
    def save_dicom(self, dataset: Dataset):
        pass

    @abstractmethod
    def find_dicom(self, query: Dataset):
        pass

    @abstractmethod
    def get_dicom(self, sop_instance_uid):
        pass
