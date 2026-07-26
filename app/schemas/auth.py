from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    role: str = "Pharmacist"

class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    role: str

    class Config:
        from_attributes = True

