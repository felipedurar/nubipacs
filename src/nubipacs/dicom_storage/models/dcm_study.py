from mongoengine import Document, StringField, IntField, DynamicField, DynamicDocument, EmbeddedDocumentField
from nubipacs.dicom_storage.models.dcm_dataset import DcmDataset

class DcmStudy(Document):
    study_instance_uid = StringField(required=True)
    dataset = EmbeddedDocumentField(DcmDataset)
    meta = {
        "collection": "dcm_studies",
        'indexes': [
            'dataset.tag_0020000D',  # Study Instance UID
        ]
    }
