import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Subject, Module, Material
from app.schemas.schemas import SubjectOut, ModuleOut, MaterialOut
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Subject).order_by(Subject.order).all()


@router.get("/subjects/{subject_id}/modules", response_model=list[ModuleOut])
def list_modules(subject_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db.query(Module).filter(Module.subject_id == subject_id).order_by(Module.order).all()


@router.get("/modules/{module_id}/materials", response_model=list[MaterialOut])
def list_materials(module_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Material).filter(Material.module_id == module_id).all()


@router.get("/materials/{material_id}/file")
def get_material_file(material_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Streams the actual PDF bytes so the frontend's PDF.js viewer can render it inline."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    file_path = os.path.join(settings.media_root, material.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on server")

    return FileResponse(file_path, media_type="application/pdf", filename=material.filename)
