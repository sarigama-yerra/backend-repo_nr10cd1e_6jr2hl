"""
Database Schemas

Mystical Team app collections.
Each Pydantic model represents a collection (lowercased name) in MongoDB.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime


class Article(BaseModel):
    """
    Articles collection schema
    Collection: "article"
    """
    title: str = Field(..., description="Article title")
    category: Literal["history", "mythology", "science"] = Field(
        ..., description="Content category"
    )
    summary: Optional[str] = Field(None, description="Short teaser or summary")
    content: str = Field(..., description="Full article content")
    image_url: Optional[HttpUrl] = Field(
        None, description="Cover image URL"
    )
    published_at: Optional[datetime] = Field(
        None, description="Original publication date if known"
    )


# You can add more collections later, e.g., Authors, Bookmarks, etc.
