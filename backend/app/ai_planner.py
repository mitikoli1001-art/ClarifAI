"""
ai_planner.py
-------------
This module is the ONLY place that talks to the LLM. Its sole job is to
turn (a) a plain-English description of what "clean" means, and (b) a
summary of the sheet's schema/sample rows, into a structured CleaningPlan
JSON object that matches schemas.CleaningPlan exactly.

Design decision: the LLM never sees or touches the full dataset, and it
never generates or executes code. It only picks values for a constrained
schema (via Claude's tool-use / structured output), which the deterministic
cleaning_engine.py then executes. This bounds what the AI can affect.
"""
import os
import json
import pandas as pd
from typing import Optional

from .schemas import CleaningPlan

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = os.getenv("CLARIFAI_MODEL", "claude-sonnet-4-6")

_CLEANING_PLAN_TOOL = {
    "name": "submit_cleaning_plan",
    "description": "Submit a structured data cleaning plan for the given spreadsheet.",
    "input_schema": CleaningPlan.model_json_schema(),
}


def _summarize_dataframe(df: pd.DataFrame, max_sample_rows: int = 5) -> str:
    lines = [f"Shape: {df.shape[0]} rows x {df.shape[1]} columns", "Columns:"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        n_nulls = int(df[col].isna().sum())
        n_unique = int(df[col].nunique(dropna=True))
        sample_vals = df[col].dropna().unique()[:3].tolist()
        lines.append(
            f"  - '{col}' | dtype={dtype} | nulls={n_nulls} | unique={n_unique} | sample={sample_vals}"
        )
    lines.append("\nSample rows:")
    lines.append(df.head(max_sample_rows).to_string())
    return "\n".join(lines)


def _fallback_heuristic_plan(df: pd.DataFrame, context_text: Optional[str]) -> CleaningPlan:
    """Used if no ANTHROPIC_API_KEY is configured, so the app still runs end-to-end.
    Applies sensible generic defaults based on column dtypes."""
    from .schemas import ColumnRule

    rules = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            rules.append(ColumnRule(column=col, dtype="float", null_strategy="fill_median"))
        elif pd.api.types.is_datetime64_any_dtype(series):
            rules.append(ColumnRule(column=col, dtype="datetime", date_format="%Y-%m-%d"))
        else:
            # try to detect date-like strings
            rules.append(
                ColumnRule(
                    column=col,
                    dtype="string",
                    standardize_case=None,
                    trim_whitespace=True,
                    null_strategy="fill_unknown",
                )
            )

    return CleaningPlan(
        drop_duplicate_rows=True,
        drop_empty_rows=True,
        drop_empty_columns=True,
        standardize_column_names=True,
        column_rules=rules,
        outlier_handling="none",
        notes=(
            "Fallback heuristic plan (no ANTHROPIC_API_KEY set): "
            "numeric columns -> median fill, text columns -> 'Unknown' fill, dedup + trim applied. "
            f"User context (not applied without AI): {context_text or 'none provided'}"
        ),
    )


def generate_cleaning_plan(df: pd.DataFrame, context_text: Optional[str]) -> CleaningPlan:
    """Main entry point: given a dataframe and a plain-English instruction,
    return a validated CleaningPlan."""
    if not ANTHROPIC_API_KEY:
        return _fallback_heuristic_plan(df, context_text)

    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    schema_summary = _summarize_dataframe(df)

    system_prompt = (
        "You are a data cleaning planning assistant. You will be given a summary "
        "of a spreadsheet's schema and sample rows, plus a plain-English description "
        "of how the user wants it cleaned. You must respond ONLY by calling the "
        "submit_cleaning_plan tool with a complete, valid plan. Do not invent columns "
        "that are not in the schema. Prefer safe, non-destructive defaults "
        "(e.g. fill_median for numeric nulls, fill_unknown for text nulls) unless the "
        "user's instructions say otherwise. Always enable drop_duplicate_rows and "
        "standardize_column_names unless the user explicitly asks not to."
    )

    user_message = (
        f"Sheet schema and sample:\n{schema_summary}\n\n"
        f"User's cleaning instructions: {context_text or 'General purpose cleaning - use safe defaults.'}"
    )

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4000,
        system=system_prompt,
        tools=[_CLEANING_PLAN_TOOL],
        tool_choice={"type": "tool", "name": "submit_cleaning_plan"},
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_cleaning_plan":
            return CleaningPlan(**block.input)

    # Safety net if the model somehow didn't call the tool
    return _fallback_heuristic_plan(df, context_text)
