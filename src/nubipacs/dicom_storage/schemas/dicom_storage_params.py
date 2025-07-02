from pydantic import BaseModel, EmailStr, IPvAnyAddress
from typing import Any, Union

from nubipacs.dicom_storage.dicom_block_storage.schemas.dicom_block_storage_params import DicomBlockStorageParams

class DicomStorageParams(BaseModel):
    metadata_db: str
    target_type: str
    params: Union[DicomBlockStorageParams, None]

