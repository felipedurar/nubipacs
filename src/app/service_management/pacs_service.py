from abc import ABC, abstractmethod

class PACSService(ABC):
    @abstractmethod
    def load_params(self, params):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def restart(self):
        pass

