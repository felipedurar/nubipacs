from fastapi import APIRouter, HTTPException
from nubipacs.database.models.user import User
from nubipacs.management.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate):
    if User.objects(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    mongo_user = User(**user.dict())
    mongo_user.save()
    return UserResponse(id=str(mongo_user.id), **user.dict())

@router.get("/", response_model=list[UserResponse])
def list_users():
    users = User.objects()
    return [UserResponse(id=str(u.id), name=u.name, email=u.email, age=u.age) for u in users]