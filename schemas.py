from pydantic import BaseModel , field_validator , Field , field_serializer
from sqlalchemy import desc

class PersonBaseSchema(BaseModel):
    name : str = Field(...,description="inter your name ...")
    @field_validator("name")
    def validate_name(cls , value):
        if len(value) < 3 :
            raise ValueError("name must be at least 3 characters")
        if len(value) > 32:
            raise ValueError("name must be at most 32 characters")
        if not value.isalpha():
            raise ValueError("name must contain only letters")
        return value
    @field_serializer("name")
    def serializer_name(value):
        return value.title()

class PersonCreateSchema(PersonBaseSchema):
    pass

class PersonResponceSchema(PersonBaseSchema):
    id : int

class PersonUpdateSchema(PersonBaseSchema):
    pass