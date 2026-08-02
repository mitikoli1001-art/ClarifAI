"""
cleaning_engine.py
------------------
This is the deterministic execution layer. It NEVER runs AI-generated code.
It only accepts a validated, structured CleaningPlan (see schemas.py) and
applies known, safe Pandas operations. This keeps cleaning auditable and
prevents arbitrary code execution risk from the AI layer.
"""
import re
import numpy as np
import pandas as pd
from typing import Tuple, Dict

from .schemas import CleaningPlan, QualityReport


def _standardize_column_name(col: str) -> str:
    col = str(col).strip()
    col = re.sub(r"[^\w\s]", "", col)          # remove special chars
    col = re.sub(r"\s+", "_", col.strip())     # spaces -> underscore
    return col.lower()


def _coerce_dtype(series: pd.Series, dtype: str) -> pd.Series:
    try:
        if dtype == "string":
            return series.astype("string")
        if dtype == "int":
            return pd.to_numeric(series, errors="coerce").astype("Int64")
        if dtype == "float":
            return pd.to_numeric(series, errors="coerce").astype("float64")
        if dtype == "datetime":
            return pd.to_datetime(series, errors="coerce")
        if dtype == "bool":
            return series.astype("boolean")
        if dtype == "category":
            return series.astype("category")
    except Exception:
        return series
    return series


def _apply_null_strategy(df: pd.DataFrame, col: str, strategy: str, fill_value=None) -> pd.DataFrame:
    if strategy == "drop_row":
        df = df[df[col].notna()]
    elif strategy == "fill_mean":
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].mean())
    elif strategy == "fill_median":
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
    elif strategy == "fill_mode":
        mode = df[col].mode(dropna=True)
        if not mode.empty:
            df[col] = df[col].fillna(mode.iloc[0])
    elif strategy == "fill_value":
        df[col] = df[col].fillna(fill_value)
    elif strategy == "fill_zero":
        df[col] = df[col].fillna(0)
    elif strategy == "fill_unknown":
        df[col] = df[col].fillna("Unknown")
    # 'leave' or unknown -> no-op
    return df


def _remove_outliers_iqr(df: pd.DataFrame, numeric_cols, mode: str) -> pd.DataFrame:
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0 or pd.isna(iqr):
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        if mode == "clip_iqr":
            # Nullable integer dtypes (Int64) can't hold fractional clip bounds -> use float64.
            if str(df[col].dtype) in ("Int64", "Int32", "Int16", "Int8", "boolean"):
                df[col] = df[col].astype("float64")
            df[col] = df[col].clip(lower, upper)
        elif mode == "remove_iqr":
            df = df[(df[col] >= lower) & (df[col] <= upper)]
    return df


def clean_dataframe(df: pd.DataFrame, plan: CleaningPlan) -> Tuple[pd.DataFrame, QualityReport]:
    df = df.copy()

    rows_before, cols_before = df.shape
    nulls_before = df.isna().sum().to_dict()
    nulls_before = {str(k): int(v) for k, v in nulls_before.items()}

    columns_dropped = []
    columns_renamed: Dict[str, str] = {}

    # 1. Drop fully empty rows/columns
    if plan.drop_empty_columns:
        empty_cols = [c for c in df.columns if df[c].isna().all()]
        columns_dropped.extend(empty_cols)
        df = df.drop(columns=empty_cols)

    if plan.drop_empty_rows:
        df = df.dropna(how="all")

    # 2. Standardize column names
    if plan.standardize_column_names:
        rename_map = {c: _standardize_column_name(c) for c in df.columns}
        # resolve collisions
        seen = {}
        for orig, new in rename_map.items():
            if new in seen:
                seen[new] += 1
                rename_map[orig] = f"{new}_{seen[new]}"
            else:
                seen[new] = 0
        df = df.rename(columns=rename_map)
        columns_renamed.update({k: v for k, v in rename_map.items() if k != v})

    # 3. Explicit column drops (post-standardization names expected, but handle both)
    for col in plan.drop_columns:
        target = _standardize_column_name(col) if plan.standardize_column_names else col
        if target in df.columns:
            df = df.drop(columns=[target])
            columns_dropped.append(target)
        elif col in df.columns:
            df = df.drop(columns=[col])
            columns_dropped.append(col)

    # 4. Per-column rules: rename, trim, case, dtype, null handling
    for rule in plan.column_rules:
        col = _standardize_column_name(rule.column) if plan.standardize_column_names else rule.column
        if col not in df.columns:
            continue

        if rule.rename_to:
            new_name = _standardize_column_name(rule.rename_to) if plan.standardize_column_names else rule.rename_to
            df = df.rename(columns={col: new_name})
            columns_renamed[col] = new_name
            col = new_name

        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
            if rule.trim_whitespace:
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            if rule.standardize_case == "lower":
                df[col] = df[col].apply(lambda x: x.lower() if isinstance(x, str) else x)
            elif rule.standardize_case == "upper":
                df[col] = df[col].apply(lambda x: x.upper() if isinstance(x, str) else x)
            elif rule.standardize_case == "title":
                df[col] = df[col].apply(lambda x: x.title() if isinstance(x, str) else x)
            if rule.remove_special_chars:
                df[col] = df[col].apply(
                    lambda x: re.sub(r"[^\w\s]", "", x) if isinstance(x, str) else x
                )

        if rule.dtype:
            df[col] = _coerce_dtype(df[col], rule.dtype)

        if rule.dtype == "datetime" and rule.date_format:
            df[col] = df[col].dt.strftime(rule.date_format)

        if rule.null_strategy:
            df = _apply_null_strategy(df, col, rule.null_strategy, rule.fill_value)

    # 5. Deduplication
    duplicates_removed = 0
    if plan.drop_duplicate_rows:
        subset = None
        if plan.duplicate_subset:
            subset = [
                _standardize_column_name(c) if plan.standardize_column_names else c
                for c in plan.duplicate_subset
            ]
            subset = [c for c in subset if c in df.columns]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=subset, keep="first")
        duplicates_removed = before_dedup - len(df)

    # 6. Outlier handling
    if plan.outlier_handling and plan.outlier_handling != "none":
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df = _remove_outliers_iqr(df, numeric_cols, plan.outlier_handling)

    df = df.reset_index(drop=True)

    nulls_after = df.isna().sum().to_dict()
    nulls_after = {str(k): int(v) for k, v in nulls_after.items()}

    report = QualityReport(
        rows_before=rows_before,
        rows_after=len(df),
        columns_before=cols_before,
        columns_after=df.shape[1],
        duplicates_removed=int(duplicates_removed),
        nulls_before=nulls_before,
        nulls_after=nulls_after,
        columns_dropped=list(dict.fromkeys(columns_dropped)),
        columns_renamed=columns_renamed,
    )
    return df, report
