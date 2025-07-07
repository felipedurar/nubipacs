from mongoengine import StringField, DynamicEmbeddedDocument

class DcmDataset(DynamicEmbeddedDocument):
    tag_00080018 = StringField()  # SOP Instance UID
    tag_0020000E = StringField()  # Series Instance UID
    tag_0020000D = StringField()  # Study Instance UID
    tag_00100020 = StringField()  # Patient ID
