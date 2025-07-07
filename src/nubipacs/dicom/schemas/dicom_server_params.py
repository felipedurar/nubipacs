from typing import List

from pydantic import BaseModel, IPvAnyAddress

from nubipacs.dicom.schemas.dicom_server_application_entity import DicomServerApplicationEntity


class DicomServerParams(BaseModel):
    ae_title: str
    bind: IPvAnyAddress
    port: int
    aplication_entities: List[DicomServerApplicationEntity]

