"""Core compensation calculations for RewardAI Professional."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .data_loader import budget_to_dict, project_to_dict, normalize_columns, validate_uploaded_data


def _num(s: pd.Series) -> pd.Series:
    if s.empty:
        return s
    return pd.to_numeric(s.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False), errors="coerce")


def parse_percent(value: Any, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    if isinstance(value, str):
        v = value.strip().replace("%", "")
        try:
            f = float(v)
        except ValueError:
            return default
        return f / 100 if f > 1 else f
    try:
        f = float(value)
    except Exception:
        return default
    return f / 100 if f > 1 else f


def pct_format(x: float | int | None) -> str:
    if x is None or pd.isna(x):
        return "N/A"
    return f"{float(x) * 100:.1f}%"


def money_format(x: float | int | None, currency: str = "SAR") -> str:
    if x is None or pd.isna(x):
        return f"{currency} 0"
    return f"{currency} {float(x):,.0f}"


def _yes(series: pd.Series) -> pd.Series:
    return series.fillna("No").astype(str).str.strip().str.lower().isin(["yes", "y", "true", "1", "critical"])


def _rating_high(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().isin(["Outstanding", "Exceeds"])


def _rating_low(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().isin(["Partially Meets", "Does Not Meet"])


def calculate_analysis(data: dict[str, pd.DataFrame], scenario: str = "Base Case") -> dict[str, Any]:
    validation = validate_uploaded_data(data)
    project = project_to_dict(data.get("Project_Setup", pd.DataFrame()))
    budget = budget_to_dict(data.get("Budget_Assumptions", pd.DataFrame()))
    currency = str(project.get("Currency", budget.get("Currency", "SAR")))

    emp = normalize_columns(data["Employee_Data"]).copy()
    struct = normalize_columns(data["Salary_Structure"]).copy()
    matrix = normalize_columns(data["Merit_Matrix"]).copy()
    market = normalize_columns(data.get("Market_Benchmark", pd.DataFrame())).copy()
    promos = normalize_columns(data.get("Promotion_Nominations", pd.DataFrame())).copy()
    critical_roles = normalize_columns(data.get("Critical_Roles", pd.DataFrame())).copy()

    for df in [emp, struct, matrix, market, promos, critical_roles]:
        for c in df.columns:
            if df[c].dtype == "object":
                df[c] = df[c].astype(str).str.strip()

    emp["Current_Base_Salary"] = _num(emp["Current_Base_Salary"]).fillna(0)
    for col in ["Minimum", "Midpoint", "Maximum"]:
        struct[col] = _num(struct[col]).fillna(0)

    analysis = emp.merge(struct[["Grade", "Minimum", "Midpoint", "Maximum", "Career_Level", "Market_Position"]], on="Grade", how="left")
    analysis["Compa_Ratio"] = np.where(analysis["Midpoint"] > 0, analysis["Current_Base_Salary"] / analysis["Midpoint"], np.nan)
    analysis["Range_Penetration"] = np.where(
        (analysis["Maximum"] - analysis["Minimum"]) > 0,
        (analysis["Current_Base_Salary"] - analysis["Minimum"]) / (analysis["Maximum"] - analysis["Minimum"]),
        np.nan,
    )
    analysis["Compa_Zone"] = np.select(
        [analysis["Compa_Ratio"] < 0.90, analysis["Compa_Ratio"] <= 1.10, analysis["Compa_Ratio"] > 1.10],
        ["Low", "Mid", "High"],
        default="Unknown",
    )
    analysis["Salary_Range_Status"] = np.select(
        [analysis["Current_Base_Salary"] < analysis["Minimum"], analysis["Current_Base_Salary"] > analysis["Maximum"]],
        ["Below Minimum", "Above Maximum"],
        default="Within Range",
    )

    matrix["Merit_Percent"] = matrix["Merit_Percent"].apply(parse_percent)
    analysis = analysis.merge(matrix[["Performance_Rating", "Compa_Zone", "Merit_Percent"]], on=["Performance_Rating", "Compa_Zone"], how="left")
    analysis["Merit_Percent"] = analysis["Merit_Percent"].fillna(0.0)

    # Scenario modifiers.
    if scenario == "Conservative":
        analysis["Scenario_Merit_Percent"] = analysis["Merit_Percent"] * 0.80
    elif scenario == "High Differentiation":
        analysis["Scenario_Merit_Percent"] = analysis["Merit_Percent"]
        analysis.loc[_rating_high(analysis["Performance_Rating"]) & (analysis["Compa_Zone"] == "Low"), "Scenario_Merit_Percent"] += 0.015
        analysis.loc[_rating_low(analysis["Performance_Rating"]), "Scenario_Merit_Percent"] *= 0.50
    elif scenario == "Critical Talent Focus":
        critical_premium = parse_percent(budget.get("Critical_Role_Premium_Percent", 0.02), 0.02)
        analysis["Scenario_Merit_Percent"] = analysis["Merit_Percent"]
        critical_bool = _yes(analysis.get("Critical_Role", pd.Series(["No"] * len(analysis))))
        analysis.loc[critical_bool & (analysis["Compa_Ratio"] < 0.95), "Scenario_Merit_Percent"] += critical_premium
    else:
        analysis["Scenario_Merit_Percent"] = analysis["Merit_Percent"]

    eligible = analysis["Eligibility"].fillna("Eligible").astype(str).str.lower().eq("eligible")
    analysis["Gross_Merit_Amount"] = np.where(eligible, analysis["Current_Base_Salary"] * analysis["Scenario_Merit_Percent"], 0)
    analysis["Salary_After_Merit_Gross"] = analysis["Current_Base_Salary"] + analysis["Gross_Merit_Amount"]
    analysis["Base_Merit_Allowed"] = np.where(
        analysis["Salary_After_Merit_Gross"] > analysis["Maximum"],
        np.maximum(analysis["Maximum"] - analysis["Current_Base_Salary"], 0),
        analysis["Gross_Merit_Amount"],
    )
    analysis["Merit_Lump_Sum"] = np.maximum(analysis["Gross_Merit_Amount"] - analysis["Base_Merit_Allowed"], 0)
    analysis["New_Base_Salary"] = analysis["Current_Base_Salary"] + analysis["Base_Merit_Allowed"]
    analysis["Final_Compa_Ratio"] = np.where(analysis["Midpoint"] > 0, analysis["New_Base_Salary"] / analysis["Midpoint"], np.nan)

    # Market benchmark merge.
    if not market.empty and {"Job_Title", "Grade", "Market_P50"}.issubset(market.columns):
        for col in ["Market_P25", "Market_P50", "Market_P75", "Market_P90"]:
            if col in market.columns:
                market[col] = _num(market[col])
        analysis = analysis.merge(
            market[[c for c in ["Job_Title", "Grade", "Market_P25", "Market_P50", "Market_P75", "Market_P90", "Market_Source"] if c in market.columns]],
            on=["Job_Title", "Grade"], how="left"
        )
        # Fallback to grade-level median when exact job benchmark is not found.
        for col in ["Market_P25", "Market_P50", "Market_P75", "Market_P90"]:
            if col in analysis.columns:
                grade_median = market.groupby("Grade")[col].median().to_dict()
                analysis[col] = analysis[col].fillna(analysis["Grade"].map(grade_median))
    else:
        for col in ["Market_P25", "Market_P50", "Market_P75", "Market_P90"]:
            analysis[col] = np.nan
        analysis["Market_Source"] = "Not Provided"

    analysis["Market_Ratio_P50"] = np.where(analysis["Market_P50"] > 0, analysis["Current_Base_Salary"] / analysis["Market_P50"], np.nan)
    analysis["Market_Ratio_P75"] = np.where(analysis["Market_P75"] > 0, analysis["Current_Base_Salary"] / analysis["Market_P75"], np.nan)
    analysis["Gap_to_P50"] = analysis["Market_P50"] - analysis["Current_Base_Salary"]
    analysis["Gap_to_P75"] = analysis["Market_P75"] - analysis["Current_Base_Salary"]

    critical_titles = set()
    if not critical_roles.empty and "Job_Title" in critical_roles.columns:
        critical_titles = set(critical_roles["Job_Title"].dropna().astype(str))
    analysis["Critical_Role_Flag"] = _yes(analysis.get("Critical_Role", pd.Series(["No"] * len(analysis)))) | analysis["Job_Title"].isin(critical_titles)

    # Risk flags long table.
    risk_rows = []
    for _, r in analysis.iterrows():
        emp_id = r.get("Employee_ID")
        name = r.get("Employee_Name")
        grade = r.get("Grade")
        dept = r.get("Department")
        def add_risk(risk_type: str, severity: str, reason: str, action: str):
            risk_rows.append([emp_id, name, dept, grade, risk_type, severity, reason, action])
        if r["Current_Base_Salary"] < r["Minimum"]:
            add_risk("Below Minimum", "High", "Current salary is below the approved range minimum.", "Review structural adjustment to at least range minimum.")
        if r["Current_Base_Salary"] > r["Maximum"]:
            add_risk("Above Maximum", "High", "Current salary is above the approved range maximum.", "Avoid base increase; consider lump-sum or freeze until range catches up.")
        if r.get("Performance_Rating") in ["Outstanding", "Exceeds"] and r.get("Compa_Ratio", 1) < 0.90:
            add_risk("High Performer Underpaid", "High", "High performance combined with compa-ratio below 90%.", "Prioritize targeted merit or market correction subject to budget.")
        if r.get("Performance_Rating") in ["Partially Meets", "Does Not Meet"] and r.get("Compa_Ratio", 0) > 1.05:
            add_risk("Low Performer Overpaid", "Medium", "Low performance combined with high compa-ratio.", "Limit base increase and review performance plan.")
        if bool(r.get("Critical_Role_Flag")) and r.get("Market_Ratio_P50", 1) < 0.90:
            add_risk("Critical Role Below Market", "High", "Critical role is below market median.", "Review market premium or retention action.")
        if pd.notna(r.get("Market_Ratio_P50")) and r.get("Market_Ratio_P50") < 0.80:
            add_risk("Market Gap Above 20%", "High", "Current salary is more than 20% below market P50.", "Review pay competitiveness and correction priority.")
        if r.get("Salary_After_Merit_Gross", 0) > r.get("Maximum", 0):
            add_risk("New Salary Above Maximum", "Medium", "Gross merit recommendation exceeds range maximum.", "Convert excess increase into lump-sum or manage through exception approval.")
    risk_flags = pd.DataFrame(risk_rows, columns=["Employee_ID", "Employee_Name", "Department", "Grade", "Risk_Type", "Severity", "Reason", "Recommended_Action"])

    # Promotions.
    promotions = pd.DataFrame()
    if not promos.empty and {"Employee_ID", "Proposed_Grade"}.issubset(promos.columns):
        promo = promos.merge(emp[["Employee_ID", "Employee_Name", "Department", "Job_Title", "Grade", "Current_Base_Salary"]], on="Employee_ID", how="left")
        new_struct = struct.rename(columns={"Grade": "Proposed_Grade", "Minimum": "New_Grade_Minimum", "Midpoint": "New_Grade_Midpoint", "Maximum": "New_Grade_Maximum"})
        promo = promo.merge(new_struct[["Proposed_Grade", "New_Grade_Minimum", "New_Grade_Midpoint", "New_Grade_Maximum"]], on="Proposed_Grade", how="left")
        default_promo = parse_percent(budget.get("Default_Promotion_Percent", 0.08), 0.08)
        promo["Promotion_Percent"] = promo.get("Promotion_Percent", default_promo).apply(lambda x: parse_percent(x, default_promo))
        promo["Policy_Increase"] = promo["Current_Base_Salary"] * promo["Promotion_Percent"]
        promo["Min_Adjustment"] = np.maximum(promo["New_Grade_Minimum"] - promo["Current_Base_Salary"], 0)
        promo["Promotion_Increase"] = np.maximum(promo["Policy_Increase"], promo["Min_Adjustment"])
        promo["Salary_After_Promotion"] = promo["Current_Base_Salary"] + promo["Promotion_Increase"]
        promo["Promotion_Flag"] = np.select(
            [promo["Salary_After_Promotion"] < promo["New_Grade_Minimum"], promo["Salary_After_Promotion"] > promo["New_Grade_Maximum"]],
            ["Below New Minimum", "Above New Maximum"],
            default="Within New Range",
        )
        promotions = promo

    eligible_payroll = analysis.loc[eligible, "Current_Base_Salary"].sum()
    merit_budget_pct = parse_percent(budget.get("Merit_Budget_Percent", 0.04), 0.04)
    promotion_budget_pct = parse_percent(budget.get("Promotion_Budget_Percent", 0.015), 0.015)
    market_budget_pct = parse_percent(budget.get("Market_Correction_Budget_Percent", 0.01), 0.01)
    lump_budget_pct = parse_percent(budget.get("Lump_Sum_Budget_Percent", 0.005), 0.005)

    merit_budget = eligible_payroll * merit_budget_pct
    promotion_budget = eligible_payroll * promotion_budget_pct
    market_budget = eligible_payroll * market_budget_pct
    lump_budget = eligible_payroll * lump_budget_pct

    proposed_merit_cost = analysis["Base_Merit_Allowed"].sum()
    lump_sum_cost = analysis["Merit_Lump_Sum"].sum()
    promotion_cost = promotions["Promotion_Increase"].sum() if not promotions.empty else 0
    # Market correction suggestion: close 25% of gap to P50 for critical/high risk cases only.
    market_corr_filter = (analysis["Critical_Role_Flag"] | _rating_high(analysis["Performance_Rating"])) & (analysis["Gap_to_P50"] > 0) & (analysis["Market_Ratio_P50"] < 0.90)
    analysis["Suggested_Market_Correction"] = np.where(market_corr_filter, analysis["Gap_to_P50"] * 0.25, 0)
    market_correction_cost = analysis["Suggested_Market_Correction"].sum()

    total_reward_cost = proposed_merit_cost + lump_sum_cost + promotion_cost + market_correction_cost
    approved_total_budget = merit_budget + promotion_budget + market_budget + lump_budget

    budget_summary = pd.DataFrame([
        ["Eligible Payroll", eligible_payroll, "Baseline payroll for eligible employees"],
        ["Approved Merit Budget", merit_budget, f"{pct_format(merit_budget_pct)} of eligible payroll"],
        ["Proposed Base Merit Cost", proposed_merit_cost, "Base salary increase cost after range maximum control"],
        ["Proposed Lump-Sum Cost", lump_sum_cost, "Excess merit converted to lump-sum"],
        ["Approved Promotion Budget", promotion_budget, f"{pct_format(promotion_budget_pct)} of eligible payroll"],
        ["Proposed Promotion Cost", promotion_cost, "Promotion nominations cost"],
        ["Approved Market Correction Budget", market_budget, f"{pct_format(market_budget_pct)} of eligible payroll"],
        ["Suggested Market Correction Cost", market_correction_cost, "Suggested targeted correction cost"],
        ["Approved Total Budget", approved_total_budget, "Merit + promotion + market + lump-sum budget"],
        ["Total Proposed Reward Cost", total_reward_cost, "Merit + lump-sum + promotion + market correction"],
        ["Budget Variance", approved_total_budget - total_reward_cost, "Positive = under budget"],
    ], columns=["Metric", "Amount", "Notes"])
    budget_utilization = total_reward_cost / approved_total_budget if approved_total_budget else np.nan

    grade_summary = analysis.groupby("Grade", dropna=False).agg(
        Headcount=("Employee_ID", "count"),
        Average_Salary=("Current_Base_Salary", "mean"),
        Average_Compa_Ratio=("Compa_Ratio", "mean"),
        Average_Market_Ratio_P50=("Market_Ratio_P50", "mean"),
        Below_Minimum=("Salary_Range_Status", lambda s: (s == "Below Minimum").sum()),
        Above_Maximum=("Salary_Range_Status", lambda s: (s == "Above Maximum").sum()),
        Proposed_Merit_Cost=("Base_Merit_Allowed", "sum"),
        Risk_Case_Count=("Employee_ID", lambda ids: risk_flags[risk_flags["Employee_ID"].isin(ids)].shape[0] if not risk_flags.empty else 0),
    ).reset_index()

    dept_summary = analysis.groupby("Department", dropna=False).agg(
        Headcount=("Employee_ID", "count"),
        Eligible_Headcount=("Eligibility", lambda s: s.astype(str).str.lower().eq("eligible").sum()),
        Average_Salary=("Current_Base_Salary", "mean"),
        Average_Compa_Ratio=("Compa_Ratio", "mean"),
        Average_Market_Ratio_P50=("Market_Ratio_P50", "mean"),
        Average_Merit_Percent=("Scenario_Merit_Percent", "mean"),
        Proposed_Cost=("Base_Merit_Allowed", "sum"),
        Risk_Case_Count=("Employee_ID", lambda ids: risk_flags[risk_flags["Employee_ID"].isin(ids)].shape[0] if not risk_flags.empty else 0),
    ).reset_index()

    scenario_comparison = build_scenario_comparison(data)

    metrics = {
        "currency": currency,
        "total_employees": int(len(analysis)),
        "eligible_employees": int(eligible.sum()),
        "current_payroll": float(analysis["Current_Base_Salary"].sum()),
        "eligible_payroll": float(eligible_payroll),
        "proposed_merit_cost": float(proposed_merit_cost),
        "lump_sum_cost": float(lump_sum_cost),
        "promotion_cost": float(promotion_cost),
        "market_correction_cost": float(market_correction_cost),
        "total_reward_cost": float(total_reward_cost),
        "approved_total_budget": float(approved_total_budget),
        "budget_utilization": float(budget_utilization) if pd.notna(budget_utilization) else 0,
        "below_minimum_cases": int((analysis["Salary_Range_Status"] == "Below Minimum").sum()),
        "above_maximum_cases": int((analysis["Salary_Range_Status"] == "Above Maximum").sum()),
        "high_performer_underpaid": int(((_rating_high(analysis["Performance_Rating"])) & (analysis["Compa_Ratio"] < 0.90)).sum()),
        "critical_role_pay_risk": int(((analysis["Critical_Role_Flag"]) & (analysis["Market_Ratio_P50"] < 0.90)).sum()),
        "risk_cases": int(len(risk_flags)),
        "scenario": scenario,
    }

    return {
        "project": project,
        "budget": budget,
        "validation": validation,
        "analysis": analysis,
        "risk_flags": risk_flags,
        "promotions": promotions,
        "budget_summary": budget_summary,
        "grade_summary": grade_summary,
        "department_summary": dept_summary,
        "scenario_comparison": scenario_comparison,
        "metrics": metrics,
    }


def build_scenario_comparison(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name in ["Base Case", "Conservative", "High Differentiation", "Critical Talent Focus"]:
        # Avoid recursive scenario comparison by using a lightweight pass without scenario comparison.
        emp = normalize_columns(data["Employee_Data"]).copy()
        struct = normalize_columns(data["Salary_Structure"]).copy()
        matrix = normalize_columns(data["Merit_Matrix"]).copy()
        budget = budget_to_dict(data.get("Budget_Assumptions", pd.DataFrame()))
        emp["Current_Base_Salary"] = _num(emp["Current_Base_Salary"]).fillna(0)
        for col in ["Minimum", "Midpoint", "Maximum"]:
            struct[col] = _num(struct[col]).fillna(0)
        matrix["Merit_Percent"] = matrix["Merit_Percent"].apply(parse_percent)
        df = emp.merge(struct[["Grade", "Minimum", "Midpoint", "Maximum"]], on="Grade", how="left")
        df["Compa_Ratio"] = np.where(df["Midpoint"] > 0, df["Current_Base_Salary"] / df["Midpoint"], np.nan)
        df["Compa_Zone"] = np.select([df["Compa_Ratio"] < 0.90, df["Compa_Ratio"] <= 1.10, df["Compa_Ratio"] > 1.10], ["Low", "Mid", "High"], default="Unknown")
        df = df.merge(matrix[["Performance_Rating", "Compa_Zone", "Merit_Percent"]], on=["Performance_Rating", "Compa_Zone"], how="left")
        df["Merit_Percent"] = df["Merit_Percent"].fillna(0)
        if name == "Conservative":
            df["Scenario_Merit_Percent"] = df["Merit_Percent"] * 0.80
            risk = "High"
            rec = "Cost control scenario; review retention exposure."
        elif name == "High Differentiation":
            df["Scenario_Merit_Percent"] = df["Merit_Percent"]
            df.loc[_rating_high(df["Performance_Rating"]) & (df["Compa_Zone"] == "Low"), "Scenario_Merit_Percent"] += 0.015
            df.loc[_rating_low(df["Performance_Rating"]), "Scenario_Merit_Percent"] *= 0.50
            risk = "Low-Medium"
            rec = "Strong pay-for-performance scenario; check budget."
        elif name == "Critical Talent Focus":
            critical_premium = parse_percent(budget.get("Critical_Role_Premium_Percent", 0.02), 0.02)
            df["Scenario_Merit_Percent"] = df["Merit_Percent"]
            critical = _yes(df.get("Critical_Role", pd.Series(["No"] * len(df))))
            df.loc[critical & (df["Compa_Ratio"] < 0.95), "Scenario_Merit_Percent"] += critical_premium
            risk = "Low"
            rec = "Recommended when retention of critical roles is the priority."
        else:
            df["Scenario_Merit_Percent"] = df["Merit_Percent"]
            risk = "Medium"
            rec = "Balanced baseline."
        eligible = df["Eligibility"].fillna("Eligible").astype(str).str.lower().eq("eligible")
        gross = np.where(eligible, df["Current_Base_Salary"] * df["Scenario_Merit_Percent"], 0)
        base_allowed = np.where(df["Current_Base_Salary"] + gross > df["Maximum"], np.maximum(df["Maximum"] - df["Current_Base_Salary"], 0), gross)
        lump = np.maximum(gross - base_allowed, 0)
        eligible_payroll = df.loc[eligible, "Current_Base_Salary"].sum()
        merit_budget = eligible_payroll * parse_percent(budget.get("Merit_Budget_Percent", 0.04), 0.04)
        rows.append([name, float(np.sum(base_allowed)), float(np.sum(lump)), float(np.sum(base_allowed) + np.sum(lump)), float((np.sum(base_allowed) + np.sum(lump)) / merit_budget if merit_budget else 0), risk, rec])
    return pd.DataFrame(rows, columns=["Scenario", "Base_Merit_Cost", "Lump_Sum_Cost", "Total_Merit_Cost", "Merit_Budget_Utilization", "Talent_Risk", "Recommendation"])
