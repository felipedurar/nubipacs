from pydantic import BaseModel, EmailStr, IPvAnyAddress
from typing import List

class DicomServerApplicationEntity(BaseModel):
    ae_title: str
    allowed_ips: List[IPvAnyAddress]
    blocked_ips: List[IPvAnyAddress]
    allowed_services: List[str]
    storage_service: str
    #storage_services: List[str]
