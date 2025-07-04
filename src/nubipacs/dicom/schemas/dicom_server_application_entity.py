from pydantic import BaseModel, EmailStr, IPvAnyAddress
from typing import List

class DicomServerApplicationEntity(BaseModel):
    ae_title: str
    ip_address: str
    port: int
    allowed_services: List[str]
    storage_service: str
    #storage_services: List[str]
