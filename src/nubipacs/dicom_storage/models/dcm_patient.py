from mongoengine import Document, StringField, IntField, DynamicField, DynamicDocument, EmbeddedDocumentField
from nubipacs.dicom_storage.models.dcm_dataset import DcmDataset

# TO BE DEFINED
class DcmPatient(Document):
    dataset = EmbeddedDocumentField(DcmDataset)
    meta = {
        "collection": "dcm_patients",
        'indexes': [
            'dataset.tag_00080018',  # SOP Instance UID
        ]
    }
