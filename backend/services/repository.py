from __future__ import annotations

import copy
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from sqlalchemy import select

from backend.api.schemas import ActivityItem, DashboardSummary, Project, ProjectOverviewResponse
from backend.core.config import Settings, get_settings
from backend.models.db import ProjectRecord, build_session_factory


class Repository(Protocol):
    def get_overview(self) -> ProjectOverviewResponse: ...
    def get_project(self, project_id: str) -> Project | None: ...
    def save_project(self, project: Project) -> Project: ...
    def append_activity(self, label: str, *, kind: str) -> None: ...
    def find_project_by_chunk(self, chunk_id: str) -> Project | None: ...


class DemoRepository:
    def __init__(self, seed_path: Path) -> None:
        self._lock = threading.Lock()
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        self._projects = {project["id"]: Project.model_validate(project) for project in seed["projects"]}
        self._activity = [ActivityItem.model_validate(item) for item in seed["activity"]]

    def _summary(self) -> DashboardSummary:
        chunks = [chunk for project in self._projects.values() for chunk in project.chunks]
        return DashboardSummary(
            totalProjects=len(self._projects),
            approvedChunks=len([chunk for chunk in chunks if chunk.status == "approved"]),
            pendingChunks=len([chunk for chunk in chunks if chunk.status == "pending"]),
            uploadedChunks=len([chunk for chunk in chunks if chunk.status == "uploaded"]),
            activeProcessingJobs=len([project for project in self._projects.values() if project.status == "processing"]),
        )

    def get_overview(self) -> ProjectOverviewResponse:
        with self._lock:
            projects = [copy.deepcopy(project) for project in self._projects.values()]
            activity = copy.deepcopy(self._activity)
        return ProjectOverviewResponse(projects=projects, activity=activity, summary=self._summary())

    def get_project(self, project_id: str) -> Project | None:
        with self._lock:
            project = self._projects.get(project_id)
            return copy.deepcopy(project) if project else None

    def save_project(self, project: Project) -> Project:
        with self._lock:
            project.updated_at = datetime.now(timezone.utc).isoformat()
            self._projects[project.id] = copy.deepcopy(project)
            return copy.deepcopy(project)

    def append_activity(self, label: str, *, kind: str) -> None:
        with self._lock:
            self._activity.insert(
                0,
                ActivityItem(
                    id=f"evt_{len(self._activity) + 100}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    label=label,
                    kind=kind,
                ),
            )
            self._activity = self._activity[:15]

    def find_project_by_chunk(self, chunk_id: str) -> Project | None:
        with self._lock:
            for project in self._projects.values():
                if any(chunk.id == chunk_id for chunk in project.chunks):
                    return copy.deepcopy(project)
        return None


class SqlAlchemyRepository:
    def __init__(self, settings: Settings) -> None:
        if not settings.database_url:
            raise ValueError("database_url is required for SqlAlchemyRepository")
        self._settings = settings
        self._session_factory, _ = build_session_factory(settings.database_url)
        seed = json.loads(settings.resolved_seed_path.read_text(encoding="utf-8"))
        self._seed_activity = [ActivityItem.model_validate(item) for item in seed["activity"]]
        self._bootstrap_seed(seed["projects"])

    def _bootstrap_seed(self, projects: list[dict]) -> None:
        with self._session_factory() as session:
            existing = session.execute(select(ProjectRecord)).scalars().first()
            if existing:
                return
            for raw_project in projects:
                parsed = Project.model_validate(raw_project)
                session.add(ProjectRecord(id=parsed.id, name=parsed.name, status=parsed.status, payload=parsed.model_dump(mode="json", by_alias=True)))
            session.commit()

    def _all_projects(self) -> list[Project]:
        with self._session_factory() as session:
            records = session.execute(select(ProjectRecord)).scalars().all()
            return [Project.model_validate(record.payload) for record in records]

    def _summary(self, projects: list[Project]) -> DashboardSummary:
        chunks = [chunk for project in projects for chunk in project.chunks]
        return DashboardSummary(
            totalProjects=len(projects),
            approvedChunks=len([chunk for chunk in chunks if chunk.status == "approved"]),
            pendingChunks=len([chunk for chunk in chunks if chunk.status == "pending"]),
            uploadedChunks=len([chunk for chunk in chunks if chunk.status == "uploaded"]),
            activeProcessingJobs=len([project for project in projects if project.status == "processing"]),
        )

    def get_overview(self) -> ProjectOverviewResponse:
        projects = self._all_projects()
        return ProjectOverviewResponse(projects=projects, activity=copy.deepcopy(self._seed_activity), summary=self._summary(projects))

    def get_project(self, project_id: str) -> Project | None:
        with self._session_factory() as session:
            record = session.get(ProjectRecord, project_id)
            return Project.model_validate(record.payload) if record else None

    def save_project(self, project: Project) -> Project:
        payload = project.model_dump(mode="json", by_alias=True)
        with self._session_factory() as session:
            record = session.get(ProjectRecord, project.id)
            if record:
                record.name = project.name
                record.status = project.status
                record.payload = payload
            else:
                session.add(ProjectRecord(id=project.id, name=project.name, status=project.status, payload=payload))
            session.commit()
        return project

    def append_activity(self, label: str, *, kind: str) -> None:
        self._seed_activity.insert(
            0,
            ActivityItem(
                id=f"evt_{len(self._seed_activity) + 500}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                label=label,
                kind=kind,
            ),
        )
        self._seed_activity = self._seed_activity[:15]

    def find_project_by_chunk(self, chunk_id: str) -> Project | None:
        for project in self._all_projects():
            if any(chunk.id == chunk_id for chunk in project.chunks):
                return project
        return None


_repository: Repository | None = None
_repository_lock = threading.Lock()


def get_repository() -> Repository:
    global _repository
    settings = get_settings()
    with _repository_lock:
        if _repository is None:
            if settings.database_url and not settings.demo_mode:
                _repository = SqlAlchemyRepository(settings)
            else:
                _repository = DemoRepository(settings.resolved_seed_path)
        return _repository
