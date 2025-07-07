from mongoengine import Document, StringField, IntField, DynamicField, DynamicDocument, EmbeddedDocumentField
from nubipacs.dicom_storage.models.dcm_dataset import DcmDataset

# TO BE DEFINED
class DcmPatient(Document):
    # The patient ID is semi-unique (institution-scoped), but for now we're going to consider it unique :)
    patient_id = StringField(required=True, unique=True)
    dataset = EmbeddedDocumentField(DcmDataset)
    meta = {
        "collection": "dcm_patients",
        'indexes': [
            'dataset.tag_00100020'   # Patient ID
        ]
    }
