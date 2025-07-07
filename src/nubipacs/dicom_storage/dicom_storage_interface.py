from abc import ABC, abstractmethod

from pydicom import Dataset
from pynetdicom.events import Event


class DicomStorageInterface(ABC):

    @abstractmethod
    def load_params(self, params):
        pass

    @abstractmethod
    def save_dicom(self, event: Event, dataset: Dataset):
        pass

    @abstractmethod
    def count_at_level(self, query: Dataset, query_retrieve_level: str):
        pass

    @abstractmethod
    def find_dicom(self, event: Event, query: Dataset):
        pass

    @abstractmethod
    def get_dicom(self, event: Event, query: Dataset):
        pass
