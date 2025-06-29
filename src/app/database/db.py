from mongoengine import connect
from app.config import settings

def init_db():
    connect(
        db=settings.MONGO_DB,
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT,
        alias="default"
    )