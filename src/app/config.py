import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_DB = os.getenv("MONGO_DB")
    MONGO_HOST = os.getenv("MONGO_HOST")
    MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

settings = Settings()