from mongoengine import connect


def init_db():
    # connect(
    #     db=settings.MONGO_DB,
    #     host=settings.MONGO_HOST,
    #     port=settings.MONGO_PORT,
    #     password=settings.MONGO_PASSWORD,
    #     alias="default"
    # )
    connect(
        host = "mongodb://admin:123456@localhost:27017/nubipacs?authSource=admin"
    )