from typing import Union

from pydantic import BaseModel

from nubipacs.dicom_storage.dicom_block_storage.schemas.dicom_block_storage_params import DicomBlockStorageParams


class DicomStorageParams(BaseModel):
    metadata_db: str
    target_type: str
    params: Union[DicomBlockStorageParams, None]

