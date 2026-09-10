from typing import Literal

from pydantic import BaseModel, Field


Jurisdiction = Literal["federal", "punjab", "sindh", "kp", "balochistan"]
Domain = Literal["constitutional", "criminal", "tenancy", "labor", "consumer"]
ChatLanguage = Literal["en", "urdu", "roman-urdu"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    jurisdiction: Jurisdiction | None = None
    province: Jurisdiction | None = None
    domain: Domain | None = None
    language: ChatLanguage = "en"


class SourceCitation(BaseModel):
    source_act: str
    section_ref: str | None = None
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    jurisdiction: Jurisdiction
    sources: list[SourceCitation]
    provider: str


class DocumentRequest(BaseModel):
    document_type: Literal["legal_notice", "fir_draft", "rental_dispute_letter"]
    language: Literal["en", "ur", "roman-urdu"] = "en"
    jurisdiction: Jurisdiction
    facts: dict[str, str] = Field(min_length=1)


class DocumentDraftRequest(BaseModel):
    document_type: Literal["legal_notice", "fir_draft", "rental_dispute_letter"]
    language: Literal["en", "ur", "roman-urdu"] = "en"
    jurisdiction: Jurisdiction
    details: dict[str, str] = Field(min_length=1)


class DocumentDraftResponse(BaseModel):
    facts: str
    requested_action: str
    provider: str


class LearnCard(BaseModel):
    title: str
    body: str
    source_act: str


class LearnResponse(BaseModel):
    domain: Domain
    jurisdiction: Jurisdiction
    cards: list[LearnCard]
    provider: str


class ChecklistRequest(BaseModel):
    document_type: Literal["legal_notice", "fir_draft", "rental_dispute_letter"]
    jurisdiction: Jurisdiction


class ChecklistResponse(BaseModel):
    items: list[str]
    provider: str
    sources: list[str]


CaseType = Literal["tenancy", "labor", "consumer", "criminal", "other"]


class CaseCreateRequest(BaseModel):
    anonymous_id: str = Field(min_length=8, max_length=100)
    case_type: CaseType
    case_date: str = Field(min_length=1, max_length=10)
    notes: str = Field(default="", max_length=10000)


class MilestoneResponse(BaseModel):
    id: str
    case_id: str
    title: str
    completed: bool
    position: int
    completed_at: str | None = None


class CaseResponse(BaseModel):
    id: str
    anonymous_id: str
    case_type: CaseType
    case_date: str
    notes: str
    created_at: str
    updated_at: str
    milestones: list[MilestoneResponse]


class MilestoneCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class MilestoneToggleRequest(BaseModel):
    completed: bool


class QuickCheckRequest(BaseModel):
    scenario: str = Field(min_length=5, max_length=2000)
    jurisdiction: Jurisdiction | None = None
    province: Jurisdiction | None = None
    domain: Domain | None = None
    language: ChatLanguage = "en"


class QuickCheckResponse(BaseModel):
    verdict: Literal["Yes", "No", "It depends"]
    reason: str
    jurisdiction: Jurisdiction
    sources: list[SourceCitation]
    provider: str