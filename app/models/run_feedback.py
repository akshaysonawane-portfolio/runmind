from pydantic import BaseModel


class RunFeedback(BaseModel):
    run_id: int
    perceived_effort: int
    felt_good: bool