from abc import ABC, abstractmethod

class PACSServiceInterface(ABC):
    name: str
    type: str

    @abstractmethod
    def load_params(self, params):
        """
        Loads the Params to the service

        :param params: The param dictionary
        :return: A boolean indicating if there was a param validation error
        """
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

