"""Sample data factory for RewardAI Professional."""
from __future__ import annotations

import pandas as pd


def sample_employee_data() -> pd.DataFrame:
    rows = [
        ["E001", "Ahmed Ali", "Finance", "Corporate", "Finance Manager", "G10", "Saudi Arabia", "SAR", 36500, "Exceeds", "Eligible", "No", "Medium", "2020-04-12", "Male", "Saudi", "Fatima Noor"],
        ["E002", "Sara Khan", "Human Resources", "Corporate", "Total Rewards Specialist", "G8", "Saudi Arabia", "SAR", 19800, "Outstanding", "Eligible", "Yes", "High", "2021-02-03", "Female", "Pakistani", "Noura Salem"],
        ["E003", "Omar Fahad", "Operations", "Operations", "Operations Supervisor", "G9", "Saudi Arabia", "SAR", 42300, "Partially Meets", "Eligible", "No", "Low", "2019-09-23", "Male", "Saudi", "Khalid Hassan"],
        ["E004", "Mariam Hassan", "IT", "Digital", "Cybersecurity Specialist", "G9", "Saudi Arabia", "SAR", 24500, "Exceeds", "Eligible", "Yes", "High", "2022-01-17", "Female", "Saudi", "Ayman Kareem"],
        ["E005", "Yousef Nasser", "Sales", "Commercial", "Sales Account Manager", "G8", "Saudi Arabia", "SAR", 27500, "Meets", "Eligible", "No", "Medium", "2021-06-10", "Male", "Egyptian", "Rami Adel"],
        ["E006", "Fatima Noor", "Finance", "Corporate", "Finance Director", "G12", "Saudi Arabia", "SAR", 71500, "Outstanding", "Eligible", "Yes", "Medium", "2018-11-04", "Female", "Saudi", "CEO"],
        ["E007", "Bilal Shah", "IT", "Digital", "Data Analyst", "G7", "Saudi Arabia", "SAR", 15000, "Exceeds", "Eligible", "Yes", "High", "2023-03-19", "Male", "Indian", "Ayman Kareem"],
        ["E008", "Lina Mansour", "Human Resources", "Corporate", "HR Business Partner", "G9", "Saudi Arabia", "SAR", 29500, "Meets", "Eligible", "No", "Low", "2020-08-08", "Female", "Lebanese", "Noura Salem"],
        ["E009", "Khalid Hassan", "Operations", "Operations", "Operations Manager", "G11", "Saudi Arabia", "SAR", 50500, "Exceeds", "Eligible", "Yes", "Medium", "2017-05-28", "Male", "Saudi", "COO"],
        ["E010", "Rami Adel", "Sales", "Commercial", "Sales Director", "G12", "Saudi Arabia", "SAR", 87500, "Outstanding", "Eligible", "Yes", "High", "2016-12-12", "Male", "Egyptian", "CEO"],
        ["E011", "Noura Salem", "Human Resources", "Corporate", "HR Manager", "G10", "Saudi Arabia", "SAR", 45500, "Meets", "Eligible", "No", "Low", "2019-04-05", "Female", "Saudi", "CHRO"],
        ["E012", "Imran Qureshi", "Operations", "Operations", "Maintenance Engineer", "G8", "Saudi Arabia", "SAR", 17000, "Exceeds", "Eligible", "No", "Medium", "2022-10-01", "Male", "Pakistani", "Khalid Hassan"],
        ["E013", "Huda Alharbi", "Finance", "Corporate", "Financial Analyst", "G7", "Saudi Arabia", "SAR", 22100, "Outstanding", "Eligible", "No", "Medium", "2023-05-15", "Female", "Saudi", "Ahmed Ali"],
        ["E014", "Ayman Kareem", "IT", "Digital", "IT Manager", "G11", "Saudi Arabia", "SAR", 40500, "Meets", "Eligible", "Yes", "Medium", "2018-02-21", "Male", "Jordanian", "CTO"],
        ["E015", "Priya Menon", "IT", "Digital", "AI Product Manager", "G10", "Saudi Arabia", "SAR", 32000, "Exceeds", "Eligible", "Yes", "High", "2024-01-08", "Female", "Indian", "Ayman Kareem"],
        ["E016", "Majed Saleh", "Operations", "Operations", "Logistics Coordinator", "G6", "Saudi Arabia", "SAR", 11200, "Meets", "Eligible", "No", "Low", "2022-07-19", "Male", "Saudi", "Khalid Hassan"],
        ["E017", "Noor Ibrahim", "Sales", "Commercial", "Sales Coordinator", "G6", "Saudi Arabia", "SAR", 18100, "Does Not Meet", "Eligible", "No", "Low", "2021-12-05", "Female", "Saudi", "Rami Adel"],
        ["E018", "Hassan Yaqoob", "Operations", "Operations", "Project Engineer", "G9", "Saudi Arabia", "SAR", 27000, "Outstanding", "Eligible", "Yes", "High", "2020-01-11", "Male", "Pakistani", "Khalid Hassan"],
        ["E019", "Ruba Nasser", "Finance", "Corporate", "Budget Analyst", "G8", "Saudi Arabia", "SAR", 23500, "Meets", "Eligible", "No", "Medium", "2023-06-30", "Female", "Jordanian", "Ahmed Ali"],
        ["E020", "Tariq Aziz", "Sales", "Commercial", "Key Account Manager", "G10", "Saudi Arabia", "SAR", 39200, "Exceeds", "Eligible", "Yes", "High", "2019-10-14", "Male", "Indian", "Rami Adel"],
        ["E021", "Mona Alotaibi", "Human Resources", "Corporate", "Learning Specialist", "G7", "Saudi Arabia", "SAR", 18800, "Meets", "Eligible", "No", "Low", "2022-04-27", "Female", "Saudi", "Noura Salem"],
        ["E022", "Jamal Faris", "IT", "Digital", "Cloud Engineer", "G9", "Saudi Arabia", "SAR", 25200, "Exceeds", "Eligible", "Yes", "High", "2021-03-21", "Male", "Lebanese", "Ayman Kareem"],
        ["E023", "Reem Abdullah", "Operations", "Operations", "Quality Manager", "G10", "Saudi Arabia", "SAR", 51500, "Partially Meets", "Eligible", "No", "Low", "2017-09-30", "Female", "Saudi", "Khalid Hassan"],
        ["E024", "Saeed Rahman", "Finance", "Corporate", "Senior Accountant", "G8", "Saudi Arabia", "SAR", 25000, "Does Not Meet", "Eligible", "No", "Low", "2018-06-18", "Male", "Bangladeshi", "Ahmed Ali"],
        ["E025", "Dalia Samir", "Human Resources", "Corporate", "Talent Acquisition Lead", "G9", "Saudi Arabia", "SAR", 31500, "Exceeds", "Eligible", "No", "Medium", "2020-12-01", "Female", "Egyptian", "Noura Salem"],
    ]
    columns = [
        "Employee_ID", "Employee_Name", "Department", "Business_Unit", "Job_Title", "Grade", "Country", "Currency",
        "Current_Base_Salary", "Performance_Rating", "Eligibility", "Critical_Role", "Flight_Risk", "Hire_Date",
        "Gender", "Nationality", "Manager_Name"
    ]
    return pd.DataFrame(rows, columns=columns)


def sample_salary_structure() -> pd.DataFrame:
    rows = [
        ["G6", 12000, 16000, 22000, "37.5%", "P50", "Associate"],
        ["G7", 15000, 20000, 27000, "35.0%", "P50", "Specialist"],
        ["G8", 18000, 24000, 33000, "37.5%", "P50", "Senior Specialist"],
        ["G9", 22000, 30000, 40000, "33.3%", "P50", "Supervisor / Lead"],
        ["G10", 28000, 38000, 50000, "31.6%", "P50-P65", "Manager"],
        ["G11", 35000, 48000, 65000, "35.4%", "P65", "Senior Manager"],
        ["G12", 45000, 62000, 85000, "37.1%", "P65-P75", "Director"],
    ]
    return pd.DataFrame(rows, columns=["Grade", "Minimum", "Midpoint", "Maximum", "Range_Spread", "Market_Position", "Career_Level"])


def sample_merit_matrix() -> pd.DataFrame:
    rows = []
    rules = {
        "Outstanding": {"Low": 0.07, "Mid": 0.06, "High": 0.04},
        "Exceeds": {"Low": 0.06, "Mid": 0.05, "High": 0.03},
        "Meets": {"Low": 0.04, "Mid": 0.03, "High": 0.02},
        "Partially Meets": {"Low": 0.01, "Mid": 0.00, "High": 0.00},
        "Does Not Meet": {"Low": 0.00, "Mid": 0.00, "High": 0.00},
    }
    for rating, zones in rules.items():
        for zone, pct in zones.items():
            rows.append([rating, zone, pct])
    return pd.DataFrame(rows, columns=["Performance_Rating", "Compa_Zone", "Merit_Percent"])


def sample_budget_assumptions() -> pd.DataFrame:
    rows = [
        ["Currency", "SAR"],
        ["Merit_Budget_Percent", 0.04],
        ["Promotion_Budget_Percent", 0.015],
        ["Market_Correction_Budget_Percent", 0.01],
        ["Lump_Sum_Budget_Percent", 0.005],
        ["Default_Promotion_Percent", 0.08],
        ["Critical_Role_Premium_Percent", 0.02],
    ]
    return pd.DataFrame(rows, columns=["Field", "Value"])


def sample_market_benchmark() -> pd.DataFrame:
    data = sample_employee_data()[["Job_Title", "Grade", "Country"]].drop_duplicates()
    grade_mid = dict(zip(sample_salary_structure()["Grade"], sample_salary_structure()["Midpoint"]))
    rows = []
    for _, row in data.iterrows():
        base = float(grade_mid[row["Grade"]])
        multiplier = 1.0
        title = row["Job_Title"].lower()
        if any(x in title for x in ["cyber", "cloud", "ai", "data"]):
            multiplier = 1.15
        elif any(x in title for x in ["sales director", "key account", "sales account"]):
            multiplier = 1.08
        elif any(x in title for x in ["operations", "maintenance", "logistics"]):
            multiplier = 0.98
        p50 = round(base * multiplier, -2)
        rows.append([row["Job_Title"], row["Grade"], row["Country"], p50 * 0.85, p50, p50 * 1.18, p50 * 1.35, "Demo Market Data"])
    return pd.DataFrame(rows, columns=["Job_Title", "Grade", "Country", "Market_P25", "Market_P50", "Market_P75", "Market_P90", "Market_Source"])


def sample_promotion_nominations() -> pd.DataFrame:
    rows = [
        ["E004", "G9", "G10", 0.08, "Expanded cybersecurity scope", "Proposed"],
        ["E007", "G7", "G8", 0.08, "High performance and scarce skill", "Proposed"],
        ["E013", "G7", "G8", 0.08, "Role expansion", "Proposed"],
        ["E018", "G9", "G10", 0.10, "Project leadership", "Proposed"],
        ["E021", "G7", "G8", 0.08, "Specialist progression", "Proposed"],
    ]
    return pd.DataFrame(rows, columns=["Employee_ID", "Current_Grade", "Proposed_Grade", "Promotion_Percent", "Promotion_Reason", "Approval_Status"])


def sample_critical_roles() -> pd.DataFrame:
    rows = [
        ["Cybersecurity Specialist", "High", "High", "P75", "Critical digital risk role"],
        ["Cloud Engineer", "High", "High", "P75", "Cloud capability scarcity"],
        ["AI Product Manager", "High", "High", "P75", "Digital product capability"],
        ["Data Analyst", "Medium", "Medium", "P65", "Analytics capability"],
        ["Key Account Manager", "High", "Medium", "P65", "Revenue critical role"],
        ["Operations Manager", "Medium", "Medium", "P65", "Operational continuity"],
    ]
    return pd.DataFrame(rows, columns=["Job_Title", "Criticality_Level", "Scarcity_Level", "Market_Position_Target", "Rationale"])


def sample_project_setup() -> pd.DataFrame:
    rows = [
        ["Company_Name", "Demo Manufacturing Company"],
        ["Country", "Saudi Arabia"],
        ["Industry", "Manufacturing / Operations"],
        ["Currency", "SAR"],
        ["Salary_Review_Year", 2026],
        ["Pay_Strategy", "P50 for core roles; P65-P75 for scarce and critical roles"],
    ]
    return pd.DataFrame(rows, columns=["Field", "Value"])


def sample_data() -> dict[str, pd.DataFrame]:
    return {
        "Project_Setup": sample_project_setup(),
        "Employee_Data": sample_employee_data(),
        "Salary_Structure": sample_salary_structure(),
        "Merit_Matrix": sample_merit_matrix(),
        "Budget_Assumptions": sample_budget_assumptions(),
        "Market_Benchmark": sample_market_benchmark(),
        "Promotion_Nominations": sample_promotion_nominations(),
        "Critical_Roles": sample_critical_roles(),
    }


def data_dictionary() -> pd.DataFrame:
    rows = [
        ["Employee_Data", "Employee_ID", "Unique employee identifier", "Required"],
        ["Employee_Data", "Current_Base_Salary", "Current monthly or annual base salary, consistent with salary structure", "Required"],
        ["Employee_Data", "Performance_Rating", "Must match Merit_Matrix ratings", "Required"],
        ["Employee_Data", "Eligibility", "Eligible or Not Eligible", "Required"],
        ["Salary_Structure", "Minimum / Midpoint / Maximum", "Salary range values by grade", "Required"],
        ["Merit_Matrix", "Merit_Percent", "Decimal percentage, e.g., 0.06 for 6%", "Required"],
        ["Market_Benchmark", "Market_P50 / P75", "Market benchmark values for comparison", "Professional"],
        ["Promotion_Nominations", "Proposed_Grade", "Target grade for promotion calculation", "Professional"],
        ["Critical_Roles", "Market_Position_Target", "Target market positioning for critical roles", "Professional"],
    ]
    return pd.DataFrame(rows, columns=["Sheet", "Column", "Description", "Requirement"])
