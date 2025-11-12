from pydantic import BaseModel

class NewsSummaryRequest(BaseModel):
    content: str
