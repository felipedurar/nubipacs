from mongoengine import Document, StringField, EmbeddedDocumentField

from nubipacs.dicom_storage.models.dcm_dataset import DcmDataset


class DcmSerie(Document):
    series_instance_uid = StringField(required=True)
    study_instance_uid = StringField(required=True)
    patient_id = StringField(required=True)
    dataset = EmbeddedDocumentField(DcmDataset)
    meta = {
        "collection": "dcm_series",
        'indexes': [
            'dataset.tag_0020000E',  # Series Instance UID
            'dataset.tag_0020000D',  # Study Instance UID
            'dataset.tag_00100020'   # Patient ID
        ]
    }
