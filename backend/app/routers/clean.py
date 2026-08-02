import os
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, CleaningJob
from ..security import get_current_user
from ..storage import load_dataframe, cleaned_output_path
from ..schemas import ContextRequest, PlanPreviewResponse, CleanExecuteRequest, CleaningPlan
from ..ai_planner import generate_cleaning_plan
from ..predefined_templates import get_predefined_plan
from ..models import CleaningTemplate
from ..cleaning_engine import clean_dataframe

router = APIRouter(prefix="/clean", tags=["clean"])


@router.post("/plan", response_model=PlanPreviewResponse)
def get_plan(payload: ContextRequest, db: Session = Depends(get_db)):
    """Resolve a cleaning plan from either: a saved template, a predefined
    template key, or a plain-English context (routed through the AI planner)."""
    try:
        df = load_dataframe(payload.file_token)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Uploaded file not found or expired")

    if payload.template_id is not None:
        template = db.query(CleaningTemplate).filter(CleaningTemplate.id == payload.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return PlanPreviewResponse(plan=CleaningPlan(**json.loads(template.plan_json)), source="saved_template")

    if payload.predefined_key:
        plan = get_predefined_plan(payload.predefined_key)
        if not plan:
            raise HTTPException(status_code=404, detail="Unknown predefined key")
        return PlanPreviewResponse(plan=plan, source="predefined")

    plan = generate_cleaning_plan(df, payload.context_text)
    return PlanPreviewResponse(plan=plan, source="ai")


@router.post("/execute")
def execute_clean(payload: CleanExecuteRequest, db: Session = Depends(get_db)):
    """Deterministically execute a (already-generated/edited) CleaningPlan
    against the uploaded sheet using pandas, and persist the result."""
    try:
        df = load_dataframe(payload.file_token)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Uploaded file not found or expired")

    cleaned_df, report = clean_dataframe(df, payload.plan)

    out_path = cleaned_output_path(payload.file_token)
    cleaned_df.to_excel(out_path, index=False)

    return {
        "file_token": payload.file_token,
        "download_ready": True,
        "quality_report": report.model_dump(),
    }


@router.get("/download/{file_token}")
def download_cleaned(file_token: str):
    path = cleaned_output_path(file_token)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Cleaned file not found. Run /clean/execute first.")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="cleaned_data.xlsx",
    )
