from mongoengine import connect
from app.config import settings

def init_db():
    # connect(
    #     db=settings.MONGO_DB,
    #     host=settings.MONGO_HOST,
    #     port=settings.MONGO_PORT,
    #     password=settings.MONGO_PASSWORD,
    #     alias="default"
    # )
    connect(
        db="nubipacs",
        username="admin",
        password="123456",
        host="localhost",
        port=27017,
        authentication_source="admin"
    )