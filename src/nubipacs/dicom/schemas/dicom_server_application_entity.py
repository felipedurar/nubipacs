from typing import List

from pydantic import BaseModel


class DicomServerApplicationEntity(BaseModel):
    ae_title: str
    ip_address: str
    port: int
    allowed_services: List[str]
    storage_service: str
    #storage_services: List[str]
