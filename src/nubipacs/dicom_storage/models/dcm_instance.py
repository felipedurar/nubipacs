from mongoengine import Document, StringField, IntField, DynamicField, DynamicDocument

class DcmInstance(DynamicDocument):
    meta = {
        "collection": "dcm_instances"
    }


