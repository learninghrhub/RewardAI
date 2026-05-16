"""Workbook loading and validation helpers for RewardAI Professional."""
from __future__ import annotations

import io
from typing import Any

import pandas as pd

from .sample_data import sample_data

REQUIRED_SHEETS = ["Employee_Data", "Salary_Structure", "Merit_Matrix", "Budget_Assumptions"]
OPTIONAL_SHEETS = ["Project_Setup", "Market_Benchmark", "Promotion_Nominations", "Critical_Roles", "Data_Dictionary"]

REQUIRED_COLUMNS = {
    "Employee_Data": [
        "Employee_ID", "Employee_Name", "Department", "Job_Title", "Grade", "Current_Base_Salary", "Performance_Rating", "Eligibility"
    ],
    "Salary_Structure": ["Grade", "Minimum", "Midpoint", "Maximum"],
    "Merit_Matrix": ["Performance_Rating", "Compa_Zone", "Merit_Percent"],
    "Budget_Assumptions": ["Field", "Value"],
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
    return df


def read_workbook(uploaded_file: Any | None = None, path: str | None = None) -> dict[str, pd.DataFrame]:
    """Read RewardAI workbook. If no file or path is provided, return sample data."""
    if uploaded_file is None and path is None:
        return sample_data()

    if uploaded_file is not None:
        content = uploaded_file.read()
        uploaded_file.seek(0)
        excel = pd.ExcelFile(io.BytesIO(content))
    else:
        excel = pd.ExcelFile(path)

    data: dict[str, pd.DataFrame] = {}
    for sheet in REQUIRED_SHEETS + OPTIONAL_SHEETS:
        if sheet in excel.sheet_names:
            data[sheet] = normalize_columns(pd.read_excel(excel, sheet_name=sheet))

    # Fill missing optional sheets with empty frames so the app can run.
    for sheet in OPTIONAL_SHEETS:
        data.setdefault(sheet, pd.DataFrame())
    return data


def budget_to_dict(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}
    df = normalize_columns(df)
    if {"Field", "Value"}.issubset(df.columns):
        return dict(zip(df["Field"].astype(str), df["Value"]))
    # Fallback: if assumptions are one row with many columns.
    return df.iloc[0].to_dict()


def project_to_dict(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}
    df = normalize_columns(df)
    if {"Field", "Value"}.issubset(df.columns):
        return dict(zip(df["Field"].astype(str), df["Value"]))
    return df.iloc[0].to_dict()


def validate_uploaded_data(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    issues = []
    for sheet in REQUIRED_SHEETS:
        if sheet not in data or data[sheet].empty:
            issues.append([sheet, "Missing required sheet", "High", "Add this sheet to the workbook."])
            continue
        df = normalize_columns(data[sheet])
        for col in REQUIRED_COLUMNS[sheet]:
            if col not in df.columns:
                issues.append([sheet, f"Missing required column: {col}", "High", "Use the blank template column names."])

    if "Employee_Data" in data and not data["Employee_Data"].empty:
        emp = normalize_columns(data["Employee_Data"])
        if "Employee_ID" in emp.columns:
            dup = emp["Employee_ID"].duplicated().sum()
            if dup > 0:
                issues.append(["Employee_Data", f"Duplicate Employee_ID rows: {dup}", "High", "Ensure each employee appears once."])
        for col in ["Current_Base_Salary", "Grade", "Performance_Rating", "Eligibility"]:
            if col in emp.columns:
                missing = emp[col].isna().sum()
                if missing > 0:
                    severity = "High" if col in ["Current_Base_Salary", "Grade"] else "Medium"
                    issues.append(["Employee_Data", f"Missing {col}: {missing}", severity, f"Populate {col} for all employees."])

    if "Salary_Structure" in data and not data["Salary_Structure"].empty and "Employee_Data" in data and not data["Employee_Data"].empty:
        emp = normalize_columns(data["Employee_Data"])
        struct = normalize_columns(data["Salary_Structure"])
        if "Grade" in emp.columns and "Grade" in struct.columns:
            emp_grades = set(emp["Grade"].dropna().astype(str))
            struct_grades = set(struct["Grade"].dropna().astype(str))
            missing_grades = sorted(emp_grades - struct_grades)
            if missing_grades:
                issues.append(["Salary_Structure", f"Grades not mapped: {', '.join(missing_grades)}", "High", "Add missing grades to Salary_Structure."])

    if "Merit_Matrix" in data and not data["Merit_Matrix"].empty and "Employee_Data" in data and not data["Employee_Data"].empty:
        emp = normalize_columns(data["Employee_Data"])
        matrix = normalize_columns(data["Merit_Matrix"])
        if "Performance_Rating" in emp.columns and "Performance_Rating" in matrix.columns:
            emp_ratings = set(emp["Performance_Rating"].dropna().astype(str).str.strip())
            matrix_ratings = set(matrix["Performance_Rating"].dropna().astype(str).str.strip())
            missing_ratings = sorted(emp_ratings - matrix_ratings)
            if missing_ratings:
                issues.append(["Merit_Matrix", f"Ratings not in matrix: {', '.join(missing_ratings)}", "High", "Add rating rows to Merit_Matrix."])

    if not issues:
        issues = [["All", "No blocking validation issues found", "Low", "Proceed to analysis."]]
    return pd.DataFrame(issues, columns=["Sheet", "Issue", "Severity", "Recommended_Action"])
