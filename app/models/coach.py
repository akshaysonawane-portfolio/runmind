from pydantic import BaseModel


class CoachQuestion(BaseModel):
    question: str