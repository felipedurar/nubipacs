from mongoengine import Document, StringField, IntField, DynamicField, DynamicDocument

class DcmInstance(DynamicDocument):
    tag_00080018 = StringField(required=True, unique=True)
    meta = {
        "collection": "dcm_instances"
        # 'indexes': [
        #     {
        #         'fields': ['tag_00080018'],
        #         'unique': True
        #     }
        # ]
    }
