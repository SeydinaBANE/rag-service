from __future__ import annotations

from pydantic import BaseModel, Field

Vector = list[float]


class Greeting(BaseModel):
    recipient: str = Field(min_length=1)
    message: str
    locale: str = "en"


class Document(BaseModel):
    doc_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class Chunk(BaseModel):
    chunk_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class ScoredChunk(BaseModel):
    chunk: Chunk
    score: float


class RagAnswer(BaseModel):
    answer: str
    sources: list[Chunk]


class DomainError(Exception):
    """Business error raised in the domain, caught in the API layer."""


class EmptyRecipientError(DomainError):
    def __init__(self) -> None:
        super().__init__("recipient must not be empty")


class EmptyQueryError(DomainError):
    def __init__(self) -> None:
        super().__init__("query must not be empty")


class EmptyCorpusError(DomainError):
    def __init__(self) -> None:
        super().__init__("no documents have been indexed")
