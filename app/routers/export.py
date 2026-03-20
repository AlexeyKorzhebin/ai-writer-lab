import io
import json
import os
import tempfile
import zipfile

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import Project, Chapter
from app.core.exporter import EPUBExporter
from app.core.pdf_exporter import PDFExporter
from app.core.docx_exporter import DOCXExporter

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])


async def _get_project_and_chapters(project_id: int, db: AsyncSession):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return None, None

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()
    return project, chapters


@router.get("/epub")
async def export_epub(project_id: int, db: AsyncSession = Depends(get_db)):
    project, chapters = await _get_project_and_chapters(project_id, db)
    if not project:
        return {"error": "Project not found"}

    exporter = EPUBExporter()
    file_path = exporter.export_project(project, chapters)
    return FileResponse(
        file_path,
        media_type="application/epub+zip",
        filename=f"{project.title}.epub",
    )


@router.get("/pdf")
async def export_pdf(project_id: int, db: AsyncSession = Depends(get_db)):
    project, chapters = await _get_project_and_chapters(project_id, db)
    if not project:
        return {"error": "Project not found"}

    exporter = PDFExporter()
    file_path = exporter.export_project(project, chapters)
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"{project.title}.pdf",
    )


@router.get("/docx")
async def export_docx(project_id: int, db: AsyncSession = Depends(get_db)):
    project, chapters = await _get_project_and_chapters(project_id, db)
    if not project:
        return {"error": "Project not found"}

    exporter = DOCXExporter()
    file_path = exporter.export_project(project, chapters)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{project.title}.docx",
    )


@router.post("/archive")
async def export_archive(project_id: int, db: AsyncSession = Depends(get_db)):
    """Export the full project as a .zip archive."""
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    import dataclasses

    project, chapters = await _get_project_and_chapters(project_id, db)
    if not project:
        return {"error": "Project not found"}

    narrative_repo = NarrativeRepository(db)
    spec = await narrative_repo.get_by_project(project_id)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            "app": "AI Writer Lab",
            "version": "0.4.0",
            "project_id": project.id,
            "title": project.title,
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        project_data = {
            "title": project.title,
            "description": project.description,
            "author_name": project.author_name,
            "author_style": project.author_style,
            "chapters": [
                {"title": c.title, "content": c.content, "summary": c.summary}
                for c in chapters
            ],
        }
        if spec:
            project_data["narrative_spec"] = json.loads(
                json.dumps(dataclasses.asdict(spec), default=str)
            )
        zf.writestr("project.json", json.dumps(project_data, ensure_ascii=False, indent=2))

        illus_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "uploads", "projects", str(project_id), "illustrations"
        )
        if os.path.isdir(illus_dir):
            for fname in os.listdir(illus_dir):
                fpath = os.path.join(illus_dir, fname)
                zf.write(fpath, f"illustrations/{fname}")

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{project.title}.zip"'},
    )
