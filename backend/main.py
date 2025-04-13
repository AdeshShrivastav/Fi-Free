# Backend (main.py)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

API_Key = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=API_Key)
model = genai.GenerativeModel('gemini-2.0-flash')

class LoanData(BaseModel):
    loan_amount: float
    loan_duration: int
    interest: float
    salary: float

class LoanData2(BaseModel):
    loan_amount: float
    loan_duration: int
    interest: float
    salary: float
    exp: float
    age: int
    loan_category: str # Added loan category

class SpentData(BaseModel):
    salary: float
    age: int  # Added age field
    location: str
    job: str

class EMICalculationRequest(BaseModel):
    principal: float
    annual_rate: float  # Annual interest rate in %
    tenure_years: int   # Loan tenure in years

class SIPCalculationRequest(BaseModel):
    monthly_investment: float
    annual_rate: float  # Annual return rate in %
    tenure_years: int

class LumpsumCalculationRequest(BaseModel):
    investment: float
    annual_rate: float  # Annual return rate in %
    tenure_years: int



# Base Models
class SIPRequest(BaseModel):
    monthly_investment: float
    annual_rate: float
    tenure_years: int

class LumpsumRequest(BaseModel):
    investment: float
    annual_rate: float
    tenure_years: int

class PPFRequest(BaseModel):
    investment: float
    annual_rate: float
    tenure_years: int

class SWPRequest(BaseModel):
    investment: float
    withdrawal: float
    annual_rate: float

class SSYRequest(BaseModel):
    investment: float
    annual_rate: float
    tenure_years: int

class EPFRequest(BaseModel):
    salary: float
    employer_percent: float
    annual_rate: float
    tenure_years: int

class NPSRequest(BaseModel):
    monthly_investment: float
    annual_rate: float
    current_age: int
    retirement_age: int

class HRARequest(BaseModel):
    salary: float
    hra: float
    rent: float
    metro: str

class SIRequest(BaseModel):
    principal: float
    annual_rate: float
    tenure_years: int

class CIRequest(BaseModel):
    principal: float
    annual_rate: float
    tenure_years: int
    frequency: int

class TaxRequest(BaseModel):
    income: float
    investment: float
    hra: float
    deductions: float

@app.post("/calculate/mf")
def sip(data: SIPRequest):
    r = data.annual_rate / 12 / 100
    n = data.tenure_years * 12
    fv = data.monthly_investment * (((1 + r)**n - 1) * (1 + r) / r)
    return {"future_value": round(fv, 2)}

@app.post("/calculate/fd")
def lumpsum(data: LumpsumRequest):
    fv = data.investment * ((1 + data.annual_rate / 100) ** data.tenure_years)
    return {"future_value": round(fv, 2)}

@app.post("/calculate/ppf")
def ppf(data: PPFRequest):
    r = data.annual_rate / 100
    n = data.tenure_years
    fv = data.investment * ((1 + r) ** n)
    return {"future_value": round(fv, 2)}

@app.post("/calculate/swp")
def swp(data: SWPRequest):
    r = data.annual_rate / 12 / 100
    months = 0
    value = data.investment
    while value > 0:
        value *= (1 + r)
        value -= data.withdrawal
        if value <= 0:
            break
        months += 1
    return {"months": months, "years": round(months / 12, 2)}

@app.post("/calculate/ssy")
def ssy(data: SSYRequest):
    r = data.annual_rate / 100
    n = data.tenure_years
    fv = data.investment * ((1 + r) ** n)
    return {"future_value": round(fv, 2)}

@app.post("/calculate/epf")
def epf(data: EPFRequest):
    monthly_contrib = data.salary * data.employer_percent / 100
    n = data.tenure_years * 12
    r = data.annual_rate / 12 / 100
    fv = monthly_contrib * ((1 + r) ** n - 1) * (1 + r) / r
    return {"future_value": round(fv, 2)}

@app.post("/calculate/nps")
def nps(data: NPSRequest):
    n = (data.retirement_age - data.current_age) * 12
    r = data.annual_rate / 12 / 100
    fv = data.monthly_investment * (((1 + r)**n - 1) * (1 + r) / r)
    return {"future_value": round(fv, 2)}

@app.post("/calculate/hra")
def hra(data: HRARequest):
    basic = data.salary
    hra_received = data.hra
    rent_paid = data.rent
    metro = data.metro.lower() == "yes"
    actual_hra = hra_received
    rent_minus_10perc = rent_paid - (0.1 * basic)
    metro_limit = 0.5 * basic if metro else 0.4 * basic
    exemption = min(actual_hra, rent_minus_10perc, metro_limit)
    return {"exempt_hra": round(exemption, 2)}

@app.post("/calculate/si")
def si(data: SIRequest):
    si = data.principal * data.annual_rate * data.tenure_years / 100
    return {"simple_interest": round(si, 2)}

@app.post("/calculate/ci")
def ci(data: CIRequest):
    r = data.annual_rate / (100 * data.frequency)
    n = data.frequency * data.tenure_years
    amount = data.principal * ((1 + r) ** n)
    return {"compound_interest": round(amount - data.principal, 2), "total_value": round(amount, 2)}

@app.post("/calculate/tax")
def tax(data: TaxRequest):
    taxable_income = data.income - (data.investment + data.hra + data.deductions)
    slabs = [(250000, 0), (250000, 0.05), (500000, 0.2), (float('inf'), 0.3)]
    tax = 0
    for limit, rate in slabs:
        if taxable_income > limit:
            tax += limit * rate
            taxable_income -= limit
        else:
            tax += taxable_income * rate
            break
    return {"tax": round(tax, 2)}
# ------------------------------
# 💰 EMI Calculator
# ------------------------------

@app.post("/calculate/emi")
def calculate_emi(data: EMICalculationRequest):
    P = data.principal
    r = data.annual_rate / 12 / 100  # monthly interest rate
    n = data.tenure_years * 12       # total number of payments

    emi = (P * r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
    total_payment = emi * n
    total_interest = total_payment - P

    return {
        "emi": round(emi, 2),
        "principal": round(P, 2),
        "interest": round(total_interest, 2)
    }

# ------------------------------
# 📈 SIP Calculator
# ------------------------------

@app.post("/calculate/sip")
def calculate_sip(data: SIPCalculationRequest):
    P = data.monthly_investment
    r = data.annual_rate / 12 / 100
    n = data.tenure_years * 12

    future_value = P * ((pow(1 + r, n) - 1) * (1 + r)) / r

    return {
        "future_value": round(future_value, 2),
        "invested_amount": round(P * n, 2),
        "returns": round(future_value - (P * n), 2)
    }

# ------------------------------
# 📊 Lumpsum Calculator
# ------------------------------

@app.post("/calculate/lumpsum")
def calculate_lumpsum(data: LumpsumCalculationRequest):
    P = data.investment
    r = data.annual_rate / 100
    n = data.tenure_years

    future_value = P * pow(1 + r, n)

    return {
        "future_value": round(future_value, 2),
        "invested_amount": round(P, 2),
        "returns": round(future_value - P, 2)
    }

@app.post("/calculate-prepayment")
async def calculate_prepayment(data: LoanData):
    # Optimized prompt for clarity and structure
    prompt = f"""
    **Role:** You are a financial planning assistant.

    **Task:** Generate a home loan prepayment analysis based on the provided details.

    **Input Data:**
    *   Loan Amount: {data.loan_amount}
    *   Original Loan Duration: {data.loan_duration} years
    *   Annual Interest Rate: {data.interest}%
    *   Monthly Salary: {data.salary}

    **Calculations Required:**
    1.  Calculate the original Monthly EMI.
    2.  Assume a minimum monthly saving of 10% of the Monthly Salary is allocated for prepayment.
    3.  Calculate the impact of making a lump-sum prepayment based on these savings accumulated over different periods:
        *   Scenario 1: Prepayment after 4 months (Prepayment Amount = 4 * 0.10 * Monthly Salary)
        *   Scenario 2: Prepayment after 6 months (Prepayment Amount = 6 * 0.10 * Monthly Salary)
        *   Scenario 3: Prepayment after 1 year (Prepayment Amount = 12 * 0.10 * Monthly Salary)
    4.  For each scenario, calculate:
        *   The new reduced loan tenure (in years and months).
        *   The total time saved compared to the original tenure (in years and months).
        *   The total interest saved compared to the original plan.

    **Output Format:**
    1.  **Primary Output (Mandatory):** A Markdown table summarizing the prepayment scenarios. The table MUST appear first.
        *   **Columns:** `Scenario Description`, `Prepayment Amount`, `Prepayment Timing`, `New Loan Tenure`, `Time Saved`, `Total Interest Saved`
        *   Include the original loan details (EMI, Total Interest without prepayment) before the table for context if helpful, but the table is the priority.
    2.  **Secondary Output:** A bulleted list summarizing the key findings and providing actionable insights or suggestions for the user regarding their prepayment strategy.

    **Strict Constraints:**
    *   DO NOT include any introductory sentences like "Here is the plan..." or identify yourself as an AI model.
    *   Start the response DIRECTLY with the Markdown table.
    *   DO NOT include any code snippets (Python, JSON, etc.) in the output.
    *   Ensure all calculations are accurate.
    *   Present the results clearly and concisely.
    """

    response = model.generate_content(prompt)
    return {"result": response.text}

@app.post("/Spent-analysis")
async def calculate_spent_analysis(data: SpentData): # Renamed function
    # Optimized prompt for clarity and structure
    prompt = f"""
    **Role:** You are a financial planning assistant specializing in budgeting and investment advice.

    **Task:** Generate a personalized monthly spending and investment plan based on the user's details.

    **Input Data:**
    *   Monthly Salary: {data.salary}
    *   Age: {data.age}
    *   Location: {data.location}
    *   Job/Business Description: {data.job}

    **Calculations & Recommendations Required:**
    1.  **Investment:** Recommend a monthly investment amount (target around 10% of salary, adjust based on overall budget). Suggest specific investment options (e.g., mutual funds, stocks, ETFs) considering the user's age (younger = higher risk tolerance, older = lower risk tolerance). Provide a sample asset allocation (e.g., % Large Cap, % Mid Cap, % Small Cap, % Stocks, % Debt/Bonds).
    2.  **Housing:** Estimate a reasonable monthly house rent budget appropriate for the specified location. If location is "not provided", give a general guideline based on salary.
    3.  **Emergency Fund:** Recommend a target amount for an emergency fund (e.g., 3-6 months of essential expenses) and suggest a monthly saving amount towards this goal.
    4.  **Expenses:** Provide a suggested monthly breakdown for essential expenses (e.g., Food, Transport, Utilities) and discretionary spending (e.g., Entertainment, Personal Care).
    5.  **Income Adequacy:** Briefly assess if the salary seems sufficient for the location and goals. If potentially insufficient, suggest considering side hustles or career advancement.

    **Output Format:**
    1.  **Primary Output (Mandatory):** A Markdown table summarizing the recommended budget allocation. The table MUST appear first .
        *   **Columns:** `Category`, `Recommended Monthly Amount/Target`, `Notes/Suggestions`
        *   Include rows for: Income (Salary), Rent, Food, Transport, Utilities, Entertainment/Personal, Emergency Fund Savings, Investment Amount, Sample Investment Allocation.
    2.  **Secondary Output:** A bulleted list summarizing the key recommendations, rationale (especially for investments based on age), and any further advice (like side hustles if needed).

    **Strict Constraints:**
    *   DO NOT include any introductory sentences like "Here is the plan..." or identify yourself as an AI model.
    *   Start the response DIRECTLY with the Markdown table.
    *   DO NOT include any code snippets (Python, JSON, etc.) in the output.
    *   Ensure all calculations and recommendations are reasonable and clearly presented.
    *   Base investment risk tolerance primarily on age as described.
    """

    response = model.generate_content(prompt)
    return {"result": response.text}


@app.post("/Loan-Analysis")
async def calculate_loan_analysis(data: LoanData2):
    # Optimized prompt for clarity and structure
    prompt = f"""
    **Role:** You are a financial advisor providing loan eligibility and affordability analysis.

    **Task:** Analyze the user's financial situation based on the provided inputs and determine if taking the specified loan is advisable and affordable. Provide a clear recommendation and supporting details.

    **Input Data:**
    *   Loan Amount: ₹{data.loan_amount}
    *   Loan Duration: {data.loan_duration} years
    *   Annual Interest Rate: {data.interest}%
    *   Monthly Salary: ₹{data.salary}
    *   Age: {data.age}
    *   Total Monthly Expenses: ₹{data.exp}
    *   Loan Category: {data.loan_category} (e.g., Home, Car, Personal, Vacation, Gadget)

    **Analysis Required:**
    1.  **Calculate Estimated Monthly EMI:** Use the standard EMI formula: EMI = P * r * (1 + r)^n / ((1 + r)^n - 1), where P = Loan Amount, r = Monthly Interest Rate (Annual Rate / 12 / 100), n = Loan Duration in months (Years * 12).
    2.  **Calculate Net Disposable Income (NDI):** NDI = Monthly Salary - Total Monthly Expenses.
    3.  **Assess Affordability:** Determine if the loan is affordable. The EMI should ideally be less than or equal to 40% of the NDI.
    4.  **Consider Age Factor:** If the user's age is above 55, advise caution or recommend against very long-term loans (e.g., > 10-15 years, depending on duration requested).
    5.  **Consider Loan Category:** Be more conservative/strict in recommending loans for non-essential categories (e.g., vacation, gadgets) compared to essential ones (e.g., home, potentially car if needed for work).
    6.  **Emergency Fund Check:** If NDI is low or expenses are very close to salary, strongly recommend building/having an emergency fund (suggest 3-6 months of expenses).
    7.  **Overall Recommendation:** Based on affordability, age, loan category, and overall financial health, provide a clear "Yes" or "No" recommendation on whether the user should consider taking the loan.

    **Output Format:**
    1.  **Primary Output (Mandatory):** A Markdown table summarizing the loan analysis. The table MUST appear first.
        *   **Columns:** `Metric`, `Value / Assessment`
        *   **Rows:** `Recommendation (Take Loan?)`, `Affordability Status`, `Estimated Monthly EMI`, `Net Disposable Income (NDI)`, `EMI as % of NDI`, `Age Consideration`, `Loan Category Consideration`
    2.  **Secondary Output:** A bulleted list providing:
        *   A brief explanation for the recommendation (Yes/No).
        *   If recommended "Yes" and affordable: A concise repayment guide including tips on budgeting for the EMI, the importance of an emergency fund, and potential prepayment strategies if applicable.
        *   If recommended "No" or "Not Affordable": Clearly state the reasons (e.g., high EMI/NDI ratio, age factor, non-essential loan category with tight finances). Include suggestions for improvement (e.g., increase income, reduce expenses, save more before taking a loan).

    **Strict Constraints:**
    *   DO NOT include any introductory sentences like "Here is the analysis..." or identify yourself as an AI model.
    *   Start the response DIRECTLY with the Markdown table.
    *   DO NOT include any code snippets (Python, JSON, etc.) in the output.
    *   Ensure all calculations (especially EMI and NDI) are accurate.
    *   Present the results clearly and concisely using Indian Rupee symbol (₹) where appropriate.
    """

    response = model.generate_content(prompt)
    return {"result": response.text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
