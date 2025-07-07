from mongoengine import Document, StringField, EmbeddedDocumentField, ListField

from nubipacs.dicom_storage.models.dcm_dataset import DcmDataset


class DcmInstance(Document):
    sop_instance_uid = StringField(required=True, unique=True)
    series_instance_uid = StringField(required=True)
    study_instance_uid = StringField(required=True)
    patient_id = StringField(required=True)
    binary_data_elements = ListField(StringField())
    dataset = EmbeddedDocumentField(DcmDataset)
    meta = {
        "collection": "dcm_instances",
        'indexes': [
            'dataset.tag_00080018',  # SOP Instance UID
            'dataset.tag_0020000E',  # Series Instance UID
            'dataset.tag_0020000D',  # Study Instance UID
            'dataset.tag_00100020'   # Patient ID
        ]
    }
