from mongoengine import Document, StringField, IntField, DynamicField

class Service(Document):
    name = StringField(required=True,unique=True)
    type = StringField(required=True)
    params = DynamicField()

    meta = {
        "collection": "services"
    }

