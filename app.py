from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.data_loader import read_workbook, validate_uploaded_data
from modules.engine import calculate_analysis, money_format, pct_format
from modules.reports import create_ai_enhanced_report, create_report
from modules.export_utils import excel_bytes, csv_bytes, docx_bytes

APP_DIR = Path(__file__).parent
SAMPLE_WORKBOOK = APP_DIR / "templates" / "rewardai_professional_sample_workbook.xlsx"
BLANK_WORKBOOK = APP_DIR / "templates" / "rewardai_professional_blank_template.xlsx"

st.set_page_config(page_title="RewardAI Professional", page_icon="💠", layout="wide")

st.markdown(
    """
<style>
    .main .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    .ra-hero {background: linear-gradient(135deg,#153c3c 0%,#0f5959 55%,#16a7a7 100%); padding: 26px 30px; border-radius: 22px; color: white; margin-bottom: 18px;}
    .ra-hero h1 {font-size: 2.1rem; margin-bottom: 0.3rem;}
    .ra-hero p {font-size: 1.02rem; opacity: 0.95; margin: 0;}
    .insight-box {border-left: 5px solid #16a7a7; background: #f3fbfb; padding: 14px 18px; border-radius: 12px; margin: 12px 0;}
    .privacy-box {background:#f8fafc; border:1px solid #dbe4e6; padding:13px 15px; border-radius:12px; font-size:0.9rem;}
    .small-note {font-size:0.85rem; color:#667085;}
    div[data-testid="stMetricValue"] {font-size: 1.35rem;}
</style>
""",
    unsafe_allow_html=True,
)


def load_template_file_bytes(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    return b""


def initialize_state():
    if "data" not in st.session_state:
        try:
            if SAMPLE_WORKBOOK.exists():
                st.session_state.data = read_workbook(path=str(SAMPLE_WORKBOOK))
            else:
                st.session_state.data = read_workbook()
        except Exception:
            st.session_state.data = read_workbook()
    if "scenario" not in st.session_state:
        st.session_state.scenario = "Base Case"
    if "report_type" not in st.session_state:
        st.session_state.report_type = "CHRO Salary Review Summary"


def build_results():
    return calculate_analysis(st.session_state.data, scenario=st.session_state.scenario)


def metric_row(metrics: dict):
    currency = metrics.get("currency", "SAR")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Employees", f"{metrics['total_employees']:,}")
    c2.metric("Eligible", f"{metrics['eligible_employees']:,}")
    c3.metric("Total Reward Cost", money_format(metrics["total_reward_cost"], currency))
    c4.metric("Budget Utilization", pct_format(metrics["budget_utilization"]))


def show_privacy_notice():
    st.markdown(
        """
<div class="privacy-box">
<b>Data privacy notice:</b> RewardAI Professional is designed for compensation analysis and decision support. Salary and employee data should be handled according to the company’s internal data privacy, confidentiality, and access control policies. For demos, use anonymized or sample data.<br>
<span class="small-note">This tool provides decision support and does not replace formal HR, finance, legal, or governance approval.</span>
</div>
""",
        unsafe_allow_html=True,
    )


def format_df(df: pd.DataFrame, pct_cols=None, money_cols=None):
    if df is None or df.empty:
        return df
    pct_cols = pct_cols or []
    money_cols = money_cols or []
    styled = df.copy()
    for c in pct_cols:
        if c in styled.columns:
            styled[c] = pd.to_numeric(styled[c], errors="coerce").map(lambda x: f"{x:.1%}" if pd.notna(x) else "")
    for c in money_cols:
        if c in styled.columns:
            styled[c] = pd.to_numeric(styled[c], errors="coerce").map(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
    return styled


initialize_state()

st.sidebar.title("💠 RewardAI")
st.sidebar.caption("Professional Compensation & Total Rewards Copilot")

uploaded = st.sidebar.file_uploader("Upload RewardAI Workbook", type=["xlsx"])
if uploaded is not None:
    try:
        st.session_state.data = read_workbook(uploaded_file=uploaded)
        st.sidebar.success("Workbook uploaded successfully.")
    except Exception as exc:
        st.sidebar.error(f"Upload error: {exc}")

if st.sidebar.button("Load Sample Data", use_container_width=True):
    st.session_state.data = read_workbook(path=str(SAMPLE_WORKBOOK)) if SAMPLE_WORKBOOK.exists() else read_workbook()
    st.sidebar.success("Sample data loaded.")

st.sidebar.download_button(
    "Download Sample Workbook",
    data=load_template_file_bytes(SAMPLE_WORKBOOK),
    file_name="rewardai_professional_sample_workbook.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
st.sidebar.download_button(
    "Download Blank Template",
    data=load_template_file_bytes(BLANK_WORKBOOK),
    file_name="rewardai_professional_blank_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

st.sidebar.divider()
st.session_state.scenario = st.sidebar.selectbox(
    "Active Scenario",
    ["Base Case", "Conservative", "High Differentiation", "Critical Talent Focus"],
    index=["Base Case", "Conservative", "High Differentiation", "Critical Talent Focus"].index(st.session_state.scenario),
)
api_key = st.sidebar.text_input("OpenAI API Key optional", type="password", help="Only needed if you want AI-enhanced report writing.")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Upload & Validation",
        "Executive Dashboard",
        "Pay Positioning",
        "Market Benchmark",
        "Merit Planner",
        "Promotion Planner",
        "Lump-Sum Planner",
        "Scenario Simulator",
        "Budget & Governance",
        "AI Reports",
        "Export Center",
        "User Guide",
    ],
)

try:
    results = build_results()
except Exception as exc:
    st.error("RewardAI could not calculate the analysis. Please review your workbook structure.")
    st.exception(exc)
    st.stop()

metrics = results["metrics"]
analysis = results["analysis"]
risk_flags = results["risk_flags"]
promotions = results["promotions"]
budget_summary = results["budget_summary"]
grade_summary = results["grade_summary"]
dept_summary = results["department_summary"]
scenario_df = results["scenario_comparison"]
currency = metrics.get("currency", "SAR")

if page == "Home":
    st.markdown(
        """
<div class="ra-hero">
<h1>RewardAI Professional</h1>
<p>From salary data to consultant-grade compensation decisions — pay positioning, market benchmarking, merit planning, promotion analysis, budget governance, and executive reports.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    metric_row(metrics)
    st.markdown("### Professional workflow")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.info("1. Upload workbook")
    c2.info("2. Validate data")
    c3.info("3. Analyze pay position")
    c4.info("4. Simulate scenarios")
    c5.info("5. Export reports")
    st.markdown(
        """
<div class="insight-box">
<b>USP:</b> RewardAI Professional turns Excel-based salary reviews into structured, fair, affordable, and leadership-ready compensation recommendations.
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("### What this version includes")
    st.write(
        "Salary structure matching, compa-ratio, range penetration, merit matrix logic, market benchmark comparison, promotion planner, lump-sum planner, scenario simulator, budget governance, risk flags, and CHRO/CFO/NRC reports."
    )

elif page == "Upload & Validation":
    st.title("Upload & Validation Center")
    show_privacy_notice()
    st.markdown("### Workbook status")
    st.write("Use the sidebar to upload a RewardAI workbook, download the sample workbook, or start from the blank template.")
    validation_df = results["validation"]
    st.dataframe(validation_df, use_container_width=True, hide_index=True)
    st.markdown("### Available sheets")
    sheet_status = pd.DataFrame([[k, len(v)] for k, v in st.session_state.data.items()], columns=["Sheet", "Rows"])
    st.dataframe(sheet_status, use_container_width=True, hide_index=True)
    st.markdown("### Required sheets")
    st.code("Employee_Data, Salary_Structure, Merit_Matrix, Budget_Assumptions", language="text")
    st.markdown("### Professional optional sheets")
    st.code("Market_Benchmark, Promotion_Nominations, Critical_Roles, Project_Setup", language="text")

elif page == "Executive Dashboard":
    st.title("Executive Dashboard")
    metric_row(metrics)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Below Minimum", metrics["below_minimum_cases"])
    c2.metric("Above Maximum", metrics["above_maximum_cases"])
    c3.metric("High Performer Underpaid", metrics["high_performer_underpaid"])
    c4.metric("Critical Role Pay Risk", metrics["critical_role_pay_risk"])

    left, right = st.columns(2)
    with left:
        st.subheader("Compa-Zone Distribution")
        zone_counts = analysis["Compa_Zone"].value_counts().reset_index()
        zone_counts.columns = ["Compa Zone", "Employees"]
        fig = px.bar(zone_counts, x="Compa Zone", y="Employees", text="Employees")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Risk Severity")
        if risk_flags.empty:
            st.success("No risk flags identified.")
        else:
            sev = risk_flags["Severity"].value_counts().reset_index()
            sev.columns = ["Severity", "Cases"]
            fig = px.pie(sev, values="Cases", names="Severity", hole=0.45)
            st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Executive insight")
    st.markdown(
        f"""
<div class="insight-box">
The active scenario is <b>{metrics['scenario']}</b>. The proposed total reward cost is <b>{money_format(metrics['total_reward_cost'], currency)}</b>, with budget utilization of <b>{pct_format(metrics['budget_utilization'])}</b>. The analysis identified <b>{metrics['risk_cases']}</b> compensation governance flags for management review.
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("### Department Summary")
    st.dataframe(format_df(dept_summary, pct_cols=["Average_Compa_Ratio", "Average_Market_Ratio_P50", "Average_Merit_Percent"], money_cols=["Average_Salary", "Proposed_Cost"]), use_container_width=True, hide_index=True)

elif page == "Pay Positioning":
    st.title("Pay Positioning")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.box(analysis, x="Grade", y="Compa_Ratio", points="all", title="Compa-Ratio by Grade")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        avg = grade_summary.sort_values("Grade")
        fig = px.bar(avg, x="Grade", y="Average_Compa_Ratio", text="Average_Compa_Ratio", title="Average Compa-Ratio by Grade")
        fig.update_yaxes(tickformat=".0%")
        fig.update_traces(texttemplate="%{text:.0%}")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Employee Pay Positioning Table")
    cols = ["Employee_ID", "Employee_Name", "Department", "Job_Title", "Grade", "Current_Base_Salary", "Minimum", "Midpoint", "Maximum", "Compa_Ratio", "Range_Penetration", "Compa_Zone", "Salary_Range_Status"]
    st.dataframe(format_df(analysis[cols], pct_cols=["Compa_Ratio", "Range_Penetration"], money_cols=["Current_Base_Salary", "Minimum", "Midpoint", "Maximum"]), use_container_width=True, hide_index=True)
    st.markdown("### Grade Summary")
    st.dataframe(format_df(grade_summary, pct_cols=["Average_Compa_Ratio", "Average_Market_Ratio_P50"], money_cols=["Average_Salary", "Proposed_Merit_Cost"]), use_container_width=True, hide_index=True)

elif page == "Market Benchmark":
    st.title("Market Benchmark Analyzer")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(analysis, x="Market_Ratio_P50", y="Compa_Ratio", color="Department", hover_data=["Employee_Name", "Job_Title", "Grade"], title="Internal Position vs Market P50")
        fig.update_xaxes(tickformat=".0%")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        gap_dept = analysis.groupby("Department", as_index=False)["Gap_to_P50"].mean().sort_values("Gap_to_P50", ascending=False)
        fig = px.bar(gap_dept, x="Department", y="Gap_to_P50", text="Gap_to_P50", title="Average Gap to Market P50 by Department")
        fig.update_traces(texttemplate="%{text:,.0f}")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Market Comparison Table")
    cols = ["Employee_ID", "Employee_Name", "Department", "Job_Title", "Grade", "Current_Base_Salary", "Market_P50", "Market_P75", "Market_Ratio_P50", "Market_Ratio_P75", "Gap_to_P50", "Gap_to_P75", "Critical_Role_Flag"]
    st.dataframe(format_df(analysis[cols], pct_cols=["Market_Ratio_P50", "Market_Ratio_P75"], money_cols=["Current_Base_Salary", "Market_P50", "Market_P75", "Gap_to_P50", "Gap_to_P75"]), use_container_width=True, hide_index=True)
    st.markdown("### Critical Role Market Risk")
    critical_risk = analysis[(analysis["Critical_Role_Flag"]) & (analysis["Market_Ratio_P50"] < 0.90)][cols]
    st.dataframe(format_df(critical_risk, pct_cols=["Market_Ratio_P50", "Market_Ratio_P75"], money_cols=["Current_Base_Salary", "Market_P50", "Market_P75", "Gap_to_P50", "Gap_to_P75"]), use_container_width=True, hide_index=True)

elif page == "Merit Planner":
    st.title("Merit Planner")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Base Merit Cost", money_format(metrics["proposed_merit_cost"], currency))
    c2.metric("Lump-Sum Cost", money_format(metrics["lump_sum_cost"], currency))
    c3.metric("Average Merit %", pct_format(analysis["Scenario_Merit_Percent"].mean()))
    c4.metric("Employees Receiving Increase", int((analysis["Gross_Merit_Amount"] > 0).sum()))
    cols = ["Employee_ID", "Employee_Name", "Department", "Grade", "Current_Base_Salary", "Performance_Rating", "Compa_Zone", "Scenario_Merit_Percent", "Gross_Merit_Amount", "Base_Merit_Allowed", "Merit_Lump_Sum", "New_Base_Salary", "Final_Compa_Ratio"]
    st.dataframe(format_df(analysis[cols], pct_cols=["Scenario_Merit_Percent", "Final_Compa_Ratio"], money_cols=["Current_Base_Salary", "Gross_Merit_Amount", "Base_Merit_Allowed", "Merit_Lump_Sum", "New_Base_Salary"]), use_container_width=True, hide_index=True)
    st.markdown("### Merit cost by department")
    cost_dept = analysis.groupby("Department", as_index=False)["Base_Merit_Allowed"].sum()
    fig = px.bar(cost_dept, x="Department", y="Base_Merit_Allowed", text="Base_Merit_Allowed")
    fig.update_traces(texttemplate="%{text:,.0f}")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Promotion Planner":
    st.title("Promotion Planner")
    if promotions.empty:
        st.info("No promotion nominations found. Add Promotion_Nominations sheet to use this module.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Promotion Nominations", len(promotions))
        c2.metric("Promotion Cost", money_format(promotions["Promotion_Increase"].sum(), currency))
        c3.metric("Avg Promotion %", pct_format((promotions["Promotion_Increase"] / promotions["Current_Base_Salary"]).mean()))
        cols = ["Employee_ID", "Employee_Name", "Department", "Job_Title", "Grade", "Proposed_Grade", "Current_Base_Salary", "New_Grade_Minimum", "New_Grade_Midpoint", "New_Grade_Maximum", "Promotion_Percent", "Promotion_Increase", "Salary_After_Promotion", "Promotion_Flag", "Promotion_Reason", "Approval_Status"]
        st.dataframe(format_df(promotions[cols], pct_cols=["Promotion_Percent"], money_cols=["Current_Base_Salary", "New_Grade_Minimum", "New_Grade_Midpoint", "New_Grade_Maximum", "Promotion_Increase", "Salary_After_Promotion"]), use_container_width=True, hide_index=True)
        fig = px.bar(promotions, x="Employee_Name", y="Promotion_Increase", color="Promotion_Flag", text="Promotion_Increase", title="Promotion Cost by Employee")
        fig.update_traces(texttemplate="%{text:,.0f}")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Lump-Sum Planner":
    st.title("Lump-Sum Planner")
    lump_df = analysis[(analysis["Merit_Lump_Sum"] > 0) | (analysis["Current_Base_Salary"] >= analysis["Maximum"])].copy()
    c1, c2 = st.columns(2)
    c1.metric("Lump-Sum Candidates", len(lump_df))
    c2.metric("Total Lump-Sum Cost", money_format(analysis["Merit_Lump_Sum"].sum(), currency))
    if lump_df.empty:
        st.success("No lump-sum candidates in the active scenario.")
    else:
        cols = ["Employee_ID", "Employee_Name", "Department", "Grade", "Current_Base_Salary", "Maximum", "Performance_Rating", "Gross_Merit_Amount", "Base_Merit_Allowed", "Merit_Lump_Sum", "New_Base_Salary", "Salary_Range_Status"]
        st.dataframe(format_df(lump_df[cols], money_cols=["Current_Base_Salary", "Maximum", "Gross_Merit_Amount", "Base_Merit_Allowed", "Merit_Lump_Sum", "New_Base_Salary"]), use_container_width=True, hide_index=True)
        st.markdown(
            """
<div class="insight-box">
Lump-sum treatment is typically used when an employee is already at or above range maximum. It allows performance recognition without permanently increasing fixed payroll beyond the approved range.
</div>
""",
            unsafe_allow_html=True,
        )

elif page == "Scenario Simulator":
    st.title("Scenario Simulator")
    st.write("Compare how different merit strategies affect cost and talent risk.")
    st.dataframe(format_df(scenario_df, pct_cols=["Merit_Budget_Utilization"], money_cols=["Base_Merit_Cost", "Lump_Sum_Cost", "Total_Merit_Cost"]), use_container_width=True, hide_index=True)
    fig = px.bar(scenario_df, x="Scenario", y="Total_Merit_Cost", color="Talent_Risk", text="Total_Merit_Cost", title="Scenario Cost Comparison")
    fig.update_traces(texttemplate="%{text:,.0f}")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Scenario recommendation")
    st.markdown(
        """
<div class="insight-box">
Use <b>Base Case</b> for standard affordability, <b>Conservative</b> when cost control is critical, <b>High Differentiation</b> when stronger pay-for-performance is required, and <b>Critical Talent Focus</b> when the organization is facing retention risk in scarce roles.
</div>
""",
        unsafe_allow_html=True,
    )

elif page == "Budget & Governance":
    st.title("Budget & Governance")
    c1, c2, c3 = st.columns(3)
    c1.metric("Approved Total Budget", money_format(metrics["approved_total_budget"], currency))
    c2.metric("Total Proposed Reward Cost", money_format(metrics["total_reward_cost"], currency))
    c3.metric("Budget Utilization", pct_format(metrics["budget_utilization"]))
    st.progress(min(float(metrics["budget_utilization"]), 1.0))
    st.markdown("### Budget Summary")
    st.dataframe(format_df(budget_summary, money_cols=["Amount"]), use_container_width=True, hide_index=True)
    st.markdown("### Risk Flags")
    if risk_flags.empty:
        st.success("No risk flags identified.")
    else:
        st.dataframe(risk_flags, use_container_width=True, hide_index=True)
        risk_csv = csv_bytes(risk_flags)
        st.download_button("Download Risk Flags CSV", risk_csv, "rewardai_risk_flags.csv", "text/csv")

elif page == "AI Reports":
    st.title("AI Reports")
    show_privacy_notice()
    report_options = [
        "CHRO Salary Review Summary",
        "CFO Affordability Note",
        "NRC Approval Paper",
        "HRBP Department Report",
        "Consultant Advisory Note",
        "Manager Communication Pack",
        "Employee FAQ",
    ]
    st.session_state.report_type = st.selectbox("Select report type", report_options, index=report_options.index(st.session_state.report_type) if st.session_state.report_type in report_options else 0)
    enhanced = st.checkbox("Use OpenAI-enhanced writing", value=False, help="Requires API key in the sidebar. The report will still use calculated values only.")
    if enhanced and api_key:
        report = create_ai_enhanced_report(api_key, st.session_state.report_type, results)
    else:
        report = create_report(st.session_state.report_type, results)
    st.markdown(report)
    st.download_button("Download Report as Markdown", report.encode("utf-8"), f"rewardai_{st.session_state.report_type.lower().replace(' ', '_')}.md", "text/markdown")
    docx = docx_bytes(report)
    if docx:
        st.download_button("Download Report as Word", docx, f"rewardai_{st.session_state.report_type.lower().replace(' ', '_')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif page == "Export Center":
    st.title("Export Center")
    st.write("Export the full analysis output for review, discussion, and record keeping.")
    st.download_button(
        "Download Full Analysis Excel",
        data=excel_bytes(results),
        file_name="rewardai_professional_full_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.download_button("Download Employee Recommendations CSV", csv_bytes(analysis), "rewardai_employee_recommendations.csv", "text/csv", use_container_width=True)
    st.download_button("Download Budget Summary CSV", csv_bytes(budget_summary), "rewardai_budget_summary.csv", "text/csv", use_container_width=True)
    st.download_button("Download Risk Flags CSV", csv_bytes(risk_flags), "rewardai_risk_flags.csv", "text/csv", use_container_width=True)
    st.markdown("### Export notes")
    st.info("The Excel export includes analysis, risk flags, promotions, budget summary, grade summary, department summary, scenario comparison, and executive metrics.")

elif page == "User Guide":
    st.title("User Guide")
    st.markdown(
        """
## How to use RewardAI Professional

1. Download the sample workbook from the sidebar and test the app.
2. Download the blank template and replace sample data with client/company data.
3. Keep the sheet names and column names unchanged.
4. Upload the workbook from the sidebar.
5. Review validation issues before using results.
6. Review Pay Positioning, Market Benchmark, Merit Planner, Promotion Planner, and Budget & Governance.
7. Generate reports from the AI Reports page.
8. Export the full analysis from Export Center.

## Key formulas

- **Compa-Ratio** = Current Base Salary / Salary Range Midpoint
- **Range Penetration** = (Current Salary - Minimum) / (Maximum - Minimum)
- **Merit Amount** = Current Base Salary × Merit Percent
- **New Base Salary** = Current Salary + Base Merit Allowed
- **Budget Utilization** = Total Proposed Reward Cost / Approved Total Budget

## Governance reminders

RewardAI is a decision-support tool. Final approval should follow the organization’s HR, Finance, Legal, and governance processes.
"""
    )
