from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    age: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str