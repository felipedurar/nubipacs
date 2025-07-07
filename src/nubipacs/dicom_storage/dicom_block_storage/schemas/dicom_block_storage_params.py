from pydantic import BaseModel


class DicomBlockStorageParams(BaseModel):
    path: str

