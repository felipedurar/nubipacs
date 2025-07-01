from mongoengine import Document, StringField, IntField, DynamicField

class Service(Document):
    name = StringField(required=True,unique=True)
    description = StringField(required=False)
    type = StringField(required=True)
    params = DynamicField()

    meta = {
        "collection": "services"
    }

