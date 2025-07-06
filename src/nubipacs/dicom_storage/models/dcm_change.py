from mongoengine import Document, StringField, IntField, DynamicField, DynamicDocument, DateTimeField, BinaryField, BooleanField

class DcmChange(Document):
    study_instance_uid = StringField(required=True)
    change_datetime = DateTimeField(required=True)
    execution_started = BooleanField()
    execution_started_datetime = DateTimeField()
    #ae_title = StringField(required=True)
    meta = {
        "collection": "dcm_changes"
    }
