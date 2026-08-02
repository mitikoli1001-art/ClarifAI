from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Cleaning plan (the contract between the AI planner and Pandas engine) ----------
class ColumnRule(BaseModel):
    column: str
    dtype: Optional[str] = Field(
        None, description="target dtype: 'string','int','float','datetime','bool','category'"
    )
    null_strategy: Optional[str] = Field(
        None,
        description="one of: 'drop_row','fill_mean','fill_median','fill_mode','fill_value','fill_zero','fill_unknown','leave'",
    )
    fill_value: Optional[Any] = None
    trim_whitespace: bool = True
    standardize_case: Optional[str] = Field(None, description="'lower','upper','title', or None")
    date_format: Optional[str] = Field(None, description="target strftime format, e.g. '%Y-%m-%d'")
    remove_special_chars: bool = False
    rename_to: Optional[str] = None


class CleaningPlan(BaseModel):
    drop_duplicate_rows: bool = True
    duplicate_subset: Optional[List[str]] = None  # columns to consider for dedup; None = all columns
    drop_empty_rows: bool = True
    drop_empty_columns: bool = True
    standardize_column_names: bool = True
    column_rules: List[ColumnRule] = []
    drop_columns: List[str] = []
    outlier_handling: Optional[str] = Field(
        None, description="'none','clip_iqr','remove_iqr'"
    )
    notes: Optional[str] = None


# ---------- API payloads ----------
class ContextRequest(BaseModel):
    file_token: str
    context_text: Optional[str] = None
    predefined_key: Optional[str] = None
    template_id: Optional[int] = None


class PlanPreviewResponse(BaseModel):
    plan: CleaningPlan
    source: str  # 'ai' | 'predefined' | 'saved_template'


class SaveTemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    context_text: Optional[str] = None
    plan: CleaningPlan


class TemplateOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_predefined: int

    class Config:
        from_attributes = True


class CleanExecuteRequest(BaseModel):
    file_token: str
    plan: CleaningPlan


class QualityReport(BaseModel):
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    duplicates_removed: int
    nulls_before: Dict[str, int]
    nulls_after: Dict[str, int]
    columns_dropped: List[str]
    columns_renamed: Dict[str, str]
