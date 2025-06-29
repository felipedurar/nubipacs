from fastapi import FastAPI
from app.db import init_db
from app.routes import user

app = FastAPI(title="FastAPI + MongoEngine")

init_db()

app.include_router(user.router, prefix="/users", tags=["Users"])