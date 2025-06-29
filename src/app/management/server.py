from fastapi import FastAPI
from app.database.db import init_db
from routes import user

app = FastAPI(title="NubiPACS - Management")

init_db()

app.include_router(user.router, prefix="/users", tags=["Users"])