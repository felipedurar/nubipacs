from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int

class UserResponse(UserCreate):
    id: str