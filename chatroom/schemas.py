from pydantic import BaseModel , field_validator , Field , field_serializer
from sqlalchemy import desc

class UserRegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)
    # age : int = Field(...,gt=0 ,lt=100,description="inter your age ...")

    @field_validator("username")
    def validate_username(cls, value):
        if not value.isalnum():
            raise ValueError("username must contain only letters and numbers")
        return value

    @field_serializer("username")
    def serializer_name(value):
        return value.title()

class UserLoginSchema(BaseModel):
    username: str
    password: str

class UserUpdateSchema(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=4, max_length=100)
    age : int | None = Field(None,gt=0 ,lt=100,description="inter your age ...")

class UserResponseSchema(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True