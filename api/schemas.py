from pydantic import BaseModel, Field, validator
from typing import Optional, List

class SearchQuery(BaseModel):
    """Pydantic model for search query validation."""
    query: str = Field(..., min_length=2, max_length=500, description="The forensic search string")
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Search query cannot be only whitespace')
        return v.strip()

class QuickSearchResponse(BaseModel):
    """Schema for instant search results."""
    id: int
    content: str
    score: str

class TopicDiscoveryResponse(BaseModel):
    """Schema for thematic discovery results."""
    topic_id: int
    label: str
    keywords: List[str]
