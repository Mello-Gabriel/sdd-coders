"""Project CRUD. Isolation is enforced by Postgres RLS, not by these handlers."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, UserSession
from app.models import Project
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_visible(session: AsyncSession, project_id: uuid.UUID) -> Project:
    # RLS makes another user's project invisible -> get() returns None -> 404.
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate, user: CurrentUser, session: UserSession
) -> ProjectRead:
    project = Project(owner_id=user.id, name=payload.name, description=payload.description)
    session.add(project)
    await session.flush()
    await record_audit(
        session,
        actor_id=user.id,
        actor_role=user.role,
        action="create",
        entity_type="project",
        entity_id=str(project.id),
    )
    return ProjectRead.model_validate(project)


@router.get("")
async def list_projects(session: UserSession) -> list[ProjectRead]:
    rows = (await session.scalars(select(Project).order_by(Project.created_at))).all()
    return [ProjectRead.model_validate(project) for project in rows]


@router.get("/{project_id}")
async def get_project(project_id: uuid.UUID, session: UserSession) -> ProjectRead:
    return ProjectRead.model_validate(await _get_visible(session, project_id))


@router.patch("/{project_id}")
async def update_project(
    project_id: uuid.UUID, payload: ProjectUpdate, user: CurrentUser, session: UserSession
) -> ProjectRead:
    project = await _get_visible(session, project_id)
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    await record_audit(
        session,
        actor_id=user.id,
        actor_role=user.role,
        action="update",
        entity_type="project",
        entity_id=str(project.id),
    )
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID, user: CurrentUser, session: UserSession
) -> Response:
    project = await _get_visible(session, project_id)
    await session.delete(project)
    await record_audit(
        session,
        actor_id=user.id,
        actor_role=user.role,
        action="delete",
        entity_type="project",
        entity_id=str(project_id),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
