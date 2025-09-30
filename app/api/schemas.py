from __future__ import annotations
from typing import List
from pydantic import BaseModel, StrictStr, Field


class IngestSection(BaseModel):
    title: StrictStr = Field(..., min_length=1, description="Title of the section")
    chunks: List[StrictStr] = Field(default_factory=list, description="List of text chunks")


class IngestDocument(BaseModel):
    title: StrictStr = Field(..., min_length=1, description="Title of the document")
    sections: List[IngestSection] = Field(default_factory=list, description="List of sections in the document")