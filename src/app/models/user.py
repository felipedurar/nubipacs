from mongoengine import Document, StringField, IntField

class User(Document):
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    age = IntField()

    meta = {
        "collection": "users"
    }