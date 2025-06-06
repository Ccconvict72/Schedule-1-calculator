from pydantic import BaseModel
from typing import Optional

class Product(BaseModel):
    Name: str
    Effect: str
    Color: str
    Price: float
    Value: float
    Rank: str
    Order: int

class Additive(BaseModel):
    Name: str
    Effect: Optional[str]
    Price: float
    Rank: str

class Effect(BaseModel):
    Name: str
    Color: str
    Multiplier: float

class Transformation(BaseModel):
    Additive: str
    From: str
    To: str
