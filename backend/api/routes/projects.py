from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.api.schemas import Project, ProjectOverviewResponse
from backend.services.events import get_event_broker
from backend.services.repository import get_repository

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectOverviewResponse)
def list_projects() -> ProjectOverviewResponse:
    return get_repository().get_overview()


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    project = get_repository().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/events")
async def stream_project_events(project_id: str) -> StreamingResponse:
    return StreamingResponse(get_event_broker().stream(project_id), media_type="text/event-stream")
