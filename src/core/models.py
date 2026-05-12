from pydantic import BaseModel
from typing import List

class ChatResponse(BaseModel):
    response: str

class PsychProfile(BaseModel):
    openness: int
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int
    summary: str
    key_quotes  : List[str]