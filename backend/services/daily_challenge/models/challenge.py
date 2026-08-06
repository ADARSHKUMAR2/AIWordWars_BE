from pydantic import BaseModel
from typing import Optional

class DailyChallenge(BaseModel):
    word: str
    scrambled: str
    hint: Optional[str] = None
    category: Optional[str] = None
    date: str
