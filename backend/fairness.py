# fairness.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal

router = APIRouter(prefix="/fairness", tags=["fairness"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def compute_fairness(data: dict) -> int:
    score = 100

    # Check interest rate
    interest = data.get("interest_rate_or_apr_percent", "")
    if interest:
        try:
            rate = float(str(interest).replace("%", "").strip())
            if rate > 8:
                score -= 10
            if rate > 10:
                score -= 20
        except:
            pass

    # Early termination fee
    if data.get("early_termination_fee"):
        score -= 8

    # Warnings
    warnings = data.get("important_warnings", [])
    if warnings:
        score -= len(warnings) * 4

    # High monthly installment penalty (example)
    monthly = data.get("monthly_installment", 0)
    if isinstance(monthly, (int, float)) and monthly > 70000:
        score -= 10

    return max(score, 0)


@router.post("/analyze")
def analyze_fairness(analysis_data: dict):
    try:
        score = compute_fairness(analysis_data)
        
        risk_level = "Low"
        color = "green"
        if score < 60:
            risk_level = "HIGH RISK"
            color = "red"
        elif score < 80:
            risk_level = "Medium"
            color = "orange"

        return {
            "fairness_score": score,
            "risk_level": risk_level,
            "color": color,
            "warnings": analysis_data.get("important_warnings", []),
            "message": "Analysis completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))