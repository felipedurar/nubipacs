from mongoengine import Document, StringField, IntField, DynamicField, DynamicDocument, DateTimeField, BinaryField

class DcmChange(Document):
    study_instance_uid = StringField(required=True)
    change_datetime = DateTimeField(required=True)
    execution_started = BinaryField()
    execution_started_datetime = DateTimeField(required=True)
    meta = {
        "collection": "dcm_changes"
        # 'indexes': [
        #     {
        #         'fields': ['tag_00080018'],
        #         'unique': True
        #     }
        # ]
    }
