from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import CaseCreateRequest, CaseResponse, MilestoneCreateRequest, MilestoneResponse, MilestoneToggleRequest
from app.services.rag_service import get_supabase

router = APIRouter(prefix="/cases", tags=["cases"])

DEFAULT_MILESTONES = {
    "tenancy": ["Notice sent", "Filed with tribunal", "Hearing scheduled"],
    "labor": ["Complaint prepared", "Complaint submitted", "Hearing scheduled"],
    "consumer": ["Seller contacted", "Complaint filed", "Resolution received"],
    "criminal": ["Evidence gathered", "FIR requested", "Investigation follow-up"],
    "other": ["Issue documented", "Relevant authority contacted", "Next step planned"],
}


def _milestone(row: dict) -> MilestoneResponse:
    return MilestoneResponse(
        id=str(row["id"]), case_id=str(row["case_id"]), title=row["title"],
        completed=row["completed"], position=row["position"], completed_at=row.get("completed_at"),
    )


def _case(row: dict, milestones: list[dict]) -> CaseResponse:
    return CaseResponse(
        id=str(row["id"]), anonymous_id=row["anonymous_id"], case_type=row["case_type"],
        case_date=str(row["case_date"]), notes=row.get("notes", ""),
        created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        milestones=[_milestone(item) for item in milestones],
    )


def _check_anonymous_id(value: str) -> str:
    if len(value) < 8 or len(value) > 100:
        raise HTTPException(status_code=400, detail="Invalid anonymous ID")
    return value


@router.post("", response_model=CaseResponse)
def create_case(request: CaseCreateRequest) -> CaseResponse:
    client = get_supabase()
    case = client.table("cases").insert({"anonymous_id": _check_anonymous_id(request.anonymous_id), "case_type": request.case_type, "case_date": request.case_date, "notes": request.notes}).execute().data[0]
    milestones = [{"case_id": case["id"], "title": title, "position": index} for index, title in enumerate(DEFAULT_MILESTONES[request.case_type])]
    created = client.table("case_milestones").insert(milestones).execute().data or []
    return _case(case, created)


@router.get("", response_model=list[CaseResponse])
def list_cases(anonymous_id: str = Query(..., min_length=8, max_length=100)) -> list[CaseResponse]:
    client = get_supabase()
    cases = client.table("cases").select("*").eq("anonymous_id", _check_anonymous_id(anonymous_id)).order("created_at", desc=True).execute().data or []
    results = []
    for case in cases:
        milestones = client.table("case_milestones").select("*").eq("case_id", case["id"]).order("position").execute().data or []
        results.append(_case(case, milestones))
    return results


@router.patch("/{case_id}/milestones/{milestone_id}", response_model=MilestoneResponse)
def toggle_milestone(case_id: str, milestone_id: str, request: MilestoneToggleRequest) -> MilestoneResponse:
    client = get_supabase()
    completed_at = datetime.now(timezone.utc).isoformat() if request.completed else None
    result = client.table("case_milestones").update({"completed": request.completed, "completed_at": completed_at}).eq("id", milestone_id).eq("case_id", case_id).execute().data or []
    if not result:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return _milestone(result[0])


@router.post("/{case_id}/milestones", response_model=MilestoneResponse)
def add_milestone(case_id: str, request: MilestoneCreateRequest) -> MilestoneResponse:
    client = get_supabase()
    existing = client.table("case_milestones").select("position").eq("case_id", case_id).order("position", desc=True).limit(1).execute().data or []
    position = existing[0]["position"] + 1 if existing else 0
    result = client.table("case_milestones").insert({"case_id": case_id, "title": request.title.strip(), "position": position}).execute().data or []
    if not result:
        raise HTTPException(status_code=404, detail="Case not found")
    return _milestone(result[0])