"""AI-style report generation for RewardAI Professional."""
from __future__ import annotations

from typing import Any

import pandas as pd

from .engine import money_format, pct_format


def _top_risks(risk_flags: pd.DataFrame, n: int = 5) -> str:
    if risk_flags is None or risk_flags.empty:
        return "- No major risk flags were detected."
    summary = risk_flags.groupby(["Risk_Type", "Severity"]).size().reset_index(name="Cases").sort_values(["Severity", "Cases"], ascending=[True, False]).head(n)
    return "\n".join([f"- {row.Risk_Type}: {int(row.Cases)} case(s), severity {row.Severity}." for _, row in summary.iterrows()])


def _dept_hotspots(dept_summary: pd.DataFrame, n: int = 3) -> str:
    if dept_summary is None or dept_summary.empty:
        return "- Department summary is not available."
    hot = dept_summary.sort_values("Risk_Case_Count", ascending=False).head(n)
    return "\n".join([f"- {row.Department}: {int(row.Risk_Case_Count)} risk case(s), average compa-ratio {row.Average_Compa_Ratio:.1%}." for _, row in hot.iterrows()])


def create_report(report_type: str, results: dict[str, Any]) -> str:
    metrics = results["metrics"]
    currency = metrics.get("currency", "SAR")
    risk_flags = results.get("risk_flags", pd.DataFrame())
    dept_summary = results.get("department_summary", pd.DataFrame())
    grade_summary = results.get("grade_summary", pd.DataFrame())
    scenario_df = results.get("scenario_comparison", pd.DataFrame())

    base = f"""
# RewardAI Professional — {report_type}

## Executive Summary
RewardAI analyzed **{metrics['total_employees']} employees**, of which **{metrics['eligible_employees']}** are eligible for the current compensation review. The total proposed reward cost is **{money_format(metrics['total_reward_cost'], currency)}**, against an approved budget of **{money_format(metrics['approved_total_budget'], currency)}**, resulting in **{pct_format(metrics['budget_utilization'])} budget utilization**. The review identified **{metrics['risk_cases']} risk and governance flags**, including **{metrics['below_minimum_cases']} below-minimum case(s)**, **{metrics['above_maximum_cases']} above-maximum case(s)**, **{metrics['high_performer_underpaid']} high-performer underpaid case(s)**, and **{metrics['critical_role_pay_risk']} critical role pay risk case(s)**.

## Key Compensation Findings
- Current payroll analyzed: **{money_format(metrics['current_payroll'], currency)}**.
- Eligible payroll: **{money_format(metrics['eligible_payroll'], currency)}**.
- Proposed base merit cost: **{money_format(metrics['proposed_merit_cost'], currency)}**.
- Proposed lump-sum cost: **{money_format(metrics['lump_sum_cost'], currency)}**.
- Proposed promotion cost: **{money_format(metrics['promotion_cost'], currency)}**.
- Suggested targeted market correction cost: **{money_format(metrics['market_correction_cost'], currency)}**.

## Risk and Governance Flags
{_top_risks(risk_flags)}

## Department Hotspots
{_dept_hotspots(dept_summary)}
"""

    if report_type == "CHRO Salary Review Summary":
        return base + f"""
## CHRO Interpretation
The proposed review provides a structured and performance-linked salary decision process. It prioritizes employees with lower compa-ratios, high performance, critical role status, and market competitiveness risk. The main CHRO focus should be to confirm whether the proposed allocation appropriately balances fairness, retention, internal equity, and affordability.

## Recommended CHRO Actions
1. Review below-minimum cases before final approval.
2. Prioritize high performers below midpoint or below market median.
3. Validate critical role pay risk cases with business leaders.
4. Confirm that above-maximum cases are handled through lump-sum or controlled base pay treatment.
5. Align final communication with pay philosophy and manager briefing materials.

## Leadership Message
Management should position the cycle as a disciplined, performance-linked, and budget-controlled salary review that supports fairness, retention, and governance.
"""

    if report_type == "CFO Affordability Note":
        variance = metrics["approved_total_budget"] - metrics["total_reward_cost"]
        status = "within budget" if variance >= 0 else "above budget"
        return base + f"""
## CFO Affordability View
The proposed total reward cost is **{money_format(metrics['total_reward_cost'], currency)}**, which is **{status}** by **{money_format(abs(variance), currency)}**. Budget utilization is **{pct_format(metrics['budget_utilization'])}**.

## Cost Drivers
- Merit cost: **{money_format(metrics['proposed_merit_cost'], currency)}**.
- Lump-sum cost: **{money_format(metrics['lump_sum_cost'], currency)}**.
- Promotion cost: **{money_format(metrics['promotion_cost'], currency)}**.
- Market correction cost: **{money_format(metrics['market_correction_cost'], currency)}**.

## Finance Recommendation
Approve the compensation cycle if final exception approvals remain controlled and any market corrections are limited to critical roles, high performers, or roles with material market competitiveness risk.
"""

    if report_type == "NRC Approval Paper":
        return base + f"""
## Background
Management has completed the annual compensation review using approved salary structures, performance ratings, salary range positioning, market competitiveness indicators, and budget assumptions.

## Management Proposal
Management recommends approving the salary review with a total proposed reward cost of **{money_format(metrics['total_reward_cost'], currency)}**, representing **{pct_format(metrics['budget_utilization'])}** utilization of the approved budget.

## Compensation Principles Applied
1. Performance differentiation through merit matrix logic.
2. Salary range governance through compa-ratio and range penetration.
3. Market competitiveness review for critical and scarce roles.
4. Affordability control through budget utilization tracking.
5. Exception governance for below-minimum and above-maximum cases.

## Decision Required
The NRC is requested to approve the proposed annual compensation review, subject to final management validation of high-risk exceptions and communication governance.

## Recommended Approval Wording
“Resolved that the proposed annual salary review is approved within the stated budget envelope, subject to final management validation of exceptions and implementation in accordance with approved compensation governance principles.”
"""

    if report_type == "Consultant Advisory Note":
        scenario_text = "- Scenario data is not available."
        if not scenario_df.empty:
            best = scenario_df.sort_values("Merit_Budget_Utilization", ascending=False).iloc[0]
            scenario_text = "\n".join([f"- {row.Scenario}: {pct_format(row.Merit_Budget_Utilization)} utilization; {row.Talent_Risk} talent risk." for _, row in scenario_df.iterrows()])
        return base + f"""
## Consultant View
The compensation review is generally structured and suitable for leadership discussion. The strongest advisory focus should be on the balance between budget control and targeted retention investment.

## Scenario Observations
{scenario_text}

## Consultant Recommendation
Use the base case for standard implementation, but prepare a critical talent focus alternative for leadership discussion where scarce roles or high performers are materially below market.
"""

    if report_type == "HRBP Department Report":
        dept_md = dept_summary.to_markdown(index=False) if not dept_summary.empty else "Department summary is not available."
        return base + f"""
## HRBP Department View
HRBPs should use this report to discuss department-level pay positioning, budget impact, and employee risk cases with business leaders.

## Department Summary
{dept_md}

## HRBP Actions
1. Review department employees below minimum or below midpoint.
2. Validate manager recommendations against merit matrix logic.
3. Prepare talking points for low or zero increase cases.
4. Escalate critical role pay risks to Total Rewards.
"""

    if report_type == "Manager Communication Pack":
        return f"""
# RewardAI Professional — Manager Communication Pack

## Manager Talking Points
- Salary review decisions were based on performance rating, salary range position, eligibility, and budget availability.
- Employees lower in the salary range may receive higher merit percentages when performance supports it.
- Employees near or above range maximum may receive limited base salary movement, and in some cases lump-sum treatment may be more appropriate.
- The process is designed to support fairness, consistency, affordability, and governance.

## How to Explain the Increase
“Your salary review outcome reflects your performance, your current position in the salary range, and the available salary review budget.”

## How to Explain a Low or Zero Increase
“This outcome does not reduce the importance of your role. It reflects the combination of current salary position, performance rating, and budget policy for this cycle.”

## Employee FAQ
**Q: Why did two employees receive different increases?**  
A: Increases are differentiated based on performance and salary range position.

**Q: What is compa-ratio?**  
A: It compares current salary to the midpoint of the salary range.

**Q: Why might someone receive a lump-sum instead of base increase?**  
A: This can happen when salary is already near or above the approved range maximum.
"""

    if report_type == "Employee FAQ":
        return f"""
# RewardAI Professional — Employee Salary Review FAQ

## What factors are considered in salary review?
Performance rating, salary range position, eligibility, budget availability, and approved compensation policy.

## What is a salary range?
A salary range defines the minimum, midpoint, and maximum pay level for a grade or role.

## What is compa-ratio?
Compa-ratio compares your current salary to the salary range midpoint. A compa-ratio below 100% means salary is below midpoint; above 100% means salary is above midpoint.

## Does a high performance rating always mean the highest increase?
Not always. Salary range position and budget also influence the final increase.

## Why can increases be different across employees?
The process considers performance, pay position, role needs, and budget discipline.
"""

    return base + "\n## Recommended Management Actions\n1. Validate exceptions.\n2. Confirm budget.\n3. Prepare communication.\n4. Execute governance approvals.\n"


def create_ai_enhanced_report(api_key: str, report_type: str, results: dict[str, Any]) -> str:
    """Optionally call OpenAI for a more polished narrative. Falls back if API fails."""
    fallback = create_report(report_type, results)
    if not api_key:
        return fallback
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        metrics = results["metrics"]
        prompt = f"""
You are RewardAI Professional, a senior Total Rewards consultant.
Create a polished {report_type} using ONLY these calculated facts. Do not invent numbers.
Facts: {metrics}
Risk flags summary: {results.get('risk_flags', pd.DataFrame()).groupby(['Risk_Type','Severity']).size().reset_index(name='Cases').to_dict(orient='records') if not results.get('risk_flags', pd.DataFrame()).empty else []}
Structure: Executive Summary, Key Findings, Budget Impact, Risk & Governance Flags, Recommended Actions.
Tone: professional, analytical, CHRO/CFO/NRC ready.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or fallback
    except Exception as exc:
        return fallback + f"\n\n---\n**AI enhancement note:** OpenAI report generation was not completed: {exc}\n"
