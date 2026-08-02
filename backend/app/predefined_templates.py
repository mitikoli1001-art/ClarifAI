"""
predefined_templates.py
-----------------------
Ready-made cleaning plans for common use cases, so a user doesn't have to
type a natural-language instruction every time. Selectable by key.
"""
from .schemas import CleaningPlan, ColumnRule

PREDEFINED_TEMPLATES = {
    "sales_data": {
        "label": "Sales / Transactions Data",
        "description": "Removes duplicate order IDs, standardizes dates, fills missing revenue with 0.",
        "plan": CleaningPlan(
            drop_duplicate_rows=True,
            duplicate_subset=None,
            drop_empty_rows=True,
            drop_empty_columns=True,
            standardize_column_names=True,
            column_rules=[
                ColumnRule(column="order_id", dtype="string", null_strategy="drop_row"),
                ColumnRule(column="order_date", dtype="datetime", date_format="%Y-%m-%d"),
                ColumnRule(column="revenue", dtype="float", null_strategy="fill_zero"),
                ColumnRule(column="quantity", dtype="int", null_strategy="fill_zero"),
                ColumnRule(column="customer_name", dtype="string", standardize_case="title", null_strategy="fill_unknown"),
            ],
            outlier_handling="clip_iqr",
            notes="Predefined: Sales/Transactions",
        ),
    },
    "hr_employee_data": {
        "label": "HR / Employee Records",
        "description": "Dedupes by employee ID, standardizes names/departments, fills missing salary with median.",
        "plan": CleaningPlan(
            drop_duplicate_rows=True,
            duplicate_subset=["employee_id"],
            drop_empty_rows=True,
            drop_empty_columns=True,
            standardize_column_names=True,
            column_rules=[
                ColumnRule(column="employee_id", dtype="string", null_strategy="drop_row"),
                ColumnRule(column="full_name", dtype="string", standardize_case="title", null_strategy="fill_unknown"),
                ColumnRule(column="department", dtype="string", standardize_case="title", null_strategy="fill_unknown"),
                ColumnRule(column="joining_date", dtype="datetime", date_format="%Y-%m-%d"),
                ColumnRule(column="salary", dtype="float", null_strategy="fill_median"),
            ],
            outlier_handling="none",
            notes="Predefined: HR/Employee",
        ),
    },
    "survey_responses": {
        "label": "Survey Responses",
        "description": "Drops incomplete responses, standardizes categorical answers, trims free-text.",
        "plan": CleaningPlan(
            drop_duplicate_rows=True,
            duplicate_subset=None,
            drop_empty_rows=True,
            drop_empty_columns=True,
            standardize_column_names=True,
            column_rules=[
                ColumnRule(column="respondent_id", dtype="string", null_strategy="drop_row"),
                ColumnRule(column="response_date", dtype="datetime", date_format="%Y-%m-%d"),
                ColumnRule(column="rating", dtype="int", null_strategy="fill_median"),
                ColumnRule(column="comments", dtype="string", trim_whitespace=True, null_strategy="fill_value", fill_value=""),
            ],
            outlier_handling="none",
            notes="Predefined: Survey Responses",
        ),
    },
    "financial_statements": {
        "label": "Financial Statements",
        "description": "Strict numeric coercion, no fabricated fills for amounts (drop instead), currency cleanup.",
        "plan": CleaningPlan(
            drop_duplicate_rows=True,
            duplicate_subset=None,
            drop_empty_rows=True,
            drop_empty_columns=True,
            standardize_column_names=True,
            column_rules=[
                ColumnRule(column="transaction_id", dtype="string", null_strategy="drop_row"),
                ColumnRule(column="transaction_date", dtype="datetime", date_format="%Y-%m-%d"),
                ColumnRule(column="amount", dtype="float", null_strategy="drop_row"),
                ColumnRule(column="account_name", dtype="string", standardize_case="title", null_strategy="fill_unknown"),
            ],
            outlier_handling="none",
            notes="Predefined: Financial Statements",
        ),
    },
}


def list_predefined():
    return [
        {"key": k, "label": v["label"], "description": v["description"]}
        for k, v in PREDEFINED_TEMPLATES.items()
    ]


def get_predefined_plan(key: str):
    entry = PREDEFINED_TEMPLATES.get(key)
    return entry["plan"] if entry else None
