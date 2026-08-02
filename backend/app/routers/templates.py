import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CleaningTemplate, User
from ..schemas import SaveTemplateRequest, TemplateOut, CleaningPlan
from ..security import get_current_user
from ..predefined_templates import list_predefined

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/predefined")
def get_predefined():
    return list_predefined()


@router.get("/mine", response_model=list[TemplateOut])
def get_my_templates(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(CleaningTemplate).filter(CleaningTemplate.owner_id == user.id).all()


@router.post("/save", response_model=TemplateOut)
def save_template(
    payload: SaveTemplateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = CleaningTemplate(
        owner_id=user.id,
        name=payload.name,
        description=payload.description,
        context_text=payload.context_text,
        plan_json=payload.plan.model_dump_json(),
        is_predefined=0,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}/plan", response_model=CleaningPlan)
def get_template_plan(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = (
        db.query(CleaningTemplate)
        .filter(CleaningTemplate.id == template_id, CleaningTemplate.owner_id == user.id)
        .first()
    )
    if not template:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Template not found")
    return CleaningPlan(**json.loads(template.plan_json))
