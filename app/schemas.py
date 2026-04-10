from pydantic import BaseModel, Field
from typing import Any, List, Optional

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)

class AskResponse(BaseModel):
    status: str
    summary: Optional[str] = None
    rows: List[dict] = []
    result_type: Optional[str] = None
    chart: Optional[Any] = None
    sql: Optional[str] = None
    error: Optional[str] = None
