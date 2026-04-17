from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.schemas import Chunk, ChunkMetadataUpdateRequest, ChunkReframeRequest, ChunkReorderRequest, ChunkStatus, ChunkSubtitleUpdateRequest, ChunkTrimRequest
from backend.services.repository import get_repository

router = APIRouter(prefix="/chunks", tags=["chunks"])


def _load_project_for_chunk(chunk_id: str):
    repository = get_repository()
    project = repository.find_project_by_chunk(chunk_id)
    if not project:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return repository, project


@router.patch("/{chunk_id}/metadata", response_model=Chunk)
def update_chunk_metadata(chunk_id: str, request: ChunkMetadataUpdateRequest) -> Chunk:
    repository, project = _load_project_for_chunk(chunk_id)
    for index, chunk in enumerate(project.chunks):
        if chunk.id != chunk_id:
            continue
        if request.title is not None:
            chunk.title = request.title
        if request.description is not None:
            chunk.description = request.description
        if request.tags is not None:
            chunk.tags = request.tags
        if request.status is not None:
            chunk.status = request.status
        project.chunks[index] = chunk
        repository.save_project(project)
        return chunk
    raise HTTPException(status_code=404, detail="Chunk not found")


@router.patch("/{chunk_id}/subtitles", response_model=Chunk)
def update_chunk_subtitles(chunk_id: str, request: ChunkSubtitleUpdateRequest) -> Chunk:
    repository, project = _load_project_for_chunk(chunk_id)
    for index, chunk in enumerate(project.chunks):
        if chunk.id != chunk_id:
            continue
        chunk.subtitle_cues = request.subtitle_cues
        project.chunks[index] = chunk
        repository.save_project(project)
        return chunk
    raise HTTPException(status_code=404, detail="Chunk not found")


@router.post("/{chunk_id}/reframe", response_model=Chunk)
def reframe_chunk(chunk_id: str, request: ChunkReframeRequest) -> Chunk:
    repository, project = _load_project_for_chunk(chunk_id)
    for index, chunk in enumerate(project.chunks):
        if chunk.id != chunk_id:
            continue
        chunk.reframe.blur = request.blur
        chunk.reframe.zoom = request.zoom
        project.chunks[index] = chunk
        repository.save_project(project)
        return chunk
    raise HTTPException(status_code=404, detail="Chunk not found")


@router.post("/{chunk_id}/trim", response_model=Chunk)
def trim_chunk(chunk_id: str, request: ChunkTrimRequest) -> Chunk:
    repository, project = _load_project_for_chunk(chunk_id)
    for index, chunk in enumerate(project.chunks):
        if chunk.id != chunk_id:
            continue
        chunk.trim_range.start_seconds = request.start_seconds
        chunk.trim_range.end_seconds = request.end_seconds
        project.chunks[index] = chunk
        repository.save_project(project)
        return chunk
    raise HTTPException(status_code=404, detail="Chunk not found")


@router.post("/reorder", response_model=list[Chunk])
def reorder_chunks(request: ChunkReorderRequest) -> list[Chunk]:
    repository = get_repository()
    project = repository.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    order_map = {chunk_id: position for position, chunk_id in enumerate(request.ordered_chunk_ids, start=1)}
    project.chunks.sort(key=lambda chunk: order_map.get(chunk.id, chunk.order))
    for index, chunk in enumerate(project.chunks, start=1):
        chunk.order = index
    repository.save_project(project)
    return project.chunks


@router.post("/{chunk_id}/upload", response_model=Chunk)
def mark_chunk_uploaded(chunk_id: str) -> Chunk:
    repository, project = _load_project_for_chunk(chunk_id)
    for index, chunk in enumerate(project.chunks):
        if chunk.id != chunk_id:
            continue
        chunk.status = ChunkStatus.UPLOADED
        chunk.upload_attempts += 1
        project.chunks[index] = chunk
        repository.save_project(project)
        return chunk
    raise HTTPException(status_code=404, detail="Chunk not found")
