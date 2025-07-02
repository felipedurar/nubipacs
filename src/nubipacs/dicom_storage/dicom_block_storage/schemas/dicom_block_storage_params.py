from pydantic import BaseModel, EmailStr, IPvAnyAddress
from typing import List

class DicomBlockStorageParams(BaseModel):
    path: str

