from pydantic import BaseModel, EmailStr, IPvAnyAddress
from typing import List
from app.dicom.schemas.dicom_server_application_entity import DicomServerApplicationEntity

class DicomServerParams(BaseModel):
    ae_title: str
    bind: IPvAnyAddress
    port: int
    aplication_entities: List[DicomServerApplicationEntity]

