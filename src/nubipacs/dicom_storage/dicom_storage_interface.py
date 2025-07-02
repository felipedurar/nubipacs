from abc import ABC, abstractmethod

class DicomStorageInterface(ABC):

    @abstractmethod
    def load_params(self, params):
        pass

    @abstractmethod
    def save_dicom(self, dataset):
        pass

    @abstractmethod
    def find_dicom(self, query):
        pass

    @abstractmethod
    def get_dicom(self, sop_instance_uid):
        pass
