"""
Lease Risk Scoring Module

Calculates a comprehensive risk score (0-100) based on lease agreement terms.
Risk score uses weighted factors to assess financial and legal risks.
"""

from typing import Dict, Any, Tuple
import json


class LeaseRiskScorer:
    """
    Calculates lease risk score based on extracted lease agreement data.
    
    Risk Factors (weighted):
    - Early Termination Fee (40%) - Highest impact, major financial risk
    - Allowed Mileage (30%) - Significant concern for high-usage drivers
    - Excess Mileage Fee (20%) - Can accumulate quickly
    - Monthly Payment (5%) - Reflects affordability concern
    - Interest Rate (5%) - Cost of money indicator
    
    Score Range: 0-100
    - 0-25: Low Risk (Green)
    - 26-50: Medium Risk (Yellow)
    - 51-75: High Risk (Orange)
    - 76-100: Critical Risk (Red)
    """
    
    # Thresholds for individual risk factors
    MILEAGE_THRESHOLDS = {
        "low": 12000,      # Less than 12k/year = low risk
        "medium": 15000,   # 12k-15k/year = medium risk
        "high": 18000,     # 15k-18k/year = high risk
    }
    
    EXCESS_MILEAGE_FEE_THRESHOLDS = {
        "low": 0.15,       # Less than $0.15/mile = low risk
        "medium": 0.25,    # $0.15-$0.25/mile = medium risk
        "high": 0.35,      # More than $0.35/mile = high risk
    }
    
    TERMINATION_FEE_THRESHOLDS = {
        "low": 2000,       # Less than $2000 = low risk
        "medium": 5000,    # $2000-$5000 = medium risk
        "high": 10000,     # More than $10000 = high risk
    }
    
    MONTHLY_PAYMENT_THRESHOLDS = {
        "low": 300,        # Less than $300/month = low risk
        "medium": 500,     # $300-$500/month = medium risk
        "high": 700,       # More than $700/month = high risk
    }
    
    INTEREST_RATE_THRESHOLDS = {
        "low": 3.0,        # Less than 3% = low risk
        "medium": 6.0,     # 3%-6% = medium risk
        "high": 10.0,      # More than 10% = high risk
    }
    
    # Weights for each factor (sum = 1.0)
    FACTOR_WEIGHTS = {
        "termination_fee": 0.40,
        "mileage": 0.30,
        "excess_fee": 0.20,
        "monthly_payment": 0.05,
        "interest_rate": 0.05,
    }
    
    @staticmethod
    def _parse_numeric_value(value: Any) -> float:
        """
        Safely parse a numeric value from various formats.
        Returns 0 if parsing fails or value is None/null.
        """
        if value is None or value == "null":
            return 0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove common currency/unit symbols and whitespace
            cleaned = value.replace("$", "").replace(",", "").strip()
            if cleaned.endswith("%"):
                cleaned = cleaned[:-1]
            try:
                return float(cleaned)
            except ValueError:
                return 0
        
        return 0
    
    @staticmethod
    def _parse_tenure_months(tenure: Any) -> int:
        """
        Parse tenure string and return months.
        Handles formats like "36 months", "3 years", etc.
        """
        if tenure is None or tenure == "null":
            return 36  # Default assumption
        
        tenure_str = str(tenure).lower().strip()
        
        # Extract number from string
        import re
        numbers = re.findall(r'\d+', tenure_str)
        if not numbers:
            return 36
        
        value = int(numbers[0])
        
        # Check if it's years and convert to months
        if "year" in tenure_str:
            return value * 12
        elif "month" in tenure_str:
            return value
        else:
            # Assume months if unclear
            return value
    
    @staticmethod
    def _score_factor(actual_value: float, thresholds: Dict[str, float]) -> float:
        """
        Score a factor based on thresholds.
        Returns a value 0-100 where 0 is ideal and 100 is critical.
        """
        if actual_value == 0:
            # Missing data = increased risk (treat as medium-high)
            return 60
        
        if actual_value <= thresholds["low"]:
            return 20  # Low risk
        elif actual_value <= thresholds["medium"]:
            return 45  # Medium risk
        elif actual_value <= thresholds["high"]:
            return 70  # High risk
        else:
            return 95  # Critical risk
    
    @classmethod
    def calculate_lease_risk(cls, lease_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive lease risk score.
        
        Args:
            lease_data: Extracted lease agreement data (JSON dict)
            
        Returns:
            Dictionary containing:
            - risk_score: 0-100 numeric score
            - risk_level: "Low", "Medium", "High", or "Critical"
            - breakdown: Dict with individual factor scores and severity
            - missing_fields: List of critical fields that are null/missing
        """
        
        # Extract and parse values
        mileage = cls._parse_numeric_value(lease_data.get("Allowed Mileage"))
        excess_fee = cls._parse_numeric_value(lease_data.get("Excess Mileage Fee"))
        termination_fee = cls._parse_numeric_value(lease_data.get("Early Termination Fee"))
        monthly_payment = cls._parse_numeric_value(lease_data.get("Monthly Payment"))
        interest_rate = cls._parse_numeric_value(lease_data.get("Interest Rate"))
        tenure = cls._parse_tenure_months(lease_data.get("Tenure"))
        
        # Check for missing critical fields
        missing_fields = []
        if not lease_data.get("Allowed Mileage"):
            missing_fields.append("Allowed Mileage")
        if not lease_data.get("Early Termination Fee"):
            missing_fields.append("Early Termination Fee")
        if not lease_data.get("Monthly Payment"):
            missing_fields.append("Monthly Payment")
        
        # Adjust mileage to annual if tenure is known
        if mileage > 0 and tenure > 0:
            annual_mileage = mileage / (tenure / 12)
        else:
            annual_mileage = mileage
        
        # Score individual factors
        mileage_score = cls._score_factor(
            annual_mileage,
            cls.MILEAGE_THRESHOLDS
        )
        
        # For excess fee, we need to account for tenure (calculate per-mile average per year)
        if excess_fee > 0:
            excess_fee_score = cls._score_factor(
                excess_fee,
                cls.EXCESS_MILEAGE_FEE_THRESHOLDS
            )
        else:
            excess_fee_score = 60  # Missing data is risky
        
        termination_fee_score = cls._score_factor(
            termination_fee,
            cls.TERMINATION_FEE_THRESHOLDS
        )
        
        monthly_payment_score = cls._score_factor(
            monthly_payment,
            cls.MONTHLY_PAYMENT_THRESHOLDS
        )
        
        interest_rate_score = cls._score_factor(
            interest_rate,
            cls.INTEREST_RATE_THRESHOLDS
        )
        
        # Calculate weighted overall score
        overall_score = (
            termination_fee_score * cls.FACTOR_WEIGHTS["termination_fee"] +
            mileage_score * cls.FACTOR_WEIGHTS["mileage"] +
            excess_fee_score * cls.FACTOR_WEIGHTS["excess_fee"] +
            monthly_payment_score * cls.FACTOR_WEIGHTS["monthly_payment"] +
            interest_rate_score * cls.FACTOR_WEIGHTS["interest_rate"]
        )
        
        # Penalize for missing critical fields
        if missing_fields:
            overall_score += len(missing_fields) * 5
        
        # Cap at 100
        overall_score = min(100, overall_score)
        
        # Determine risk level
        if overall_score <= 25:
            risk_level = "Low"
        elif overall_score <= 50:
            risk_level = "Medium"
        elif overall_score <= 75:
            risk_level = "High"
        else:
            risk_level = "Critical"
        
        # Build breakdown
        breakdown = {
            "Early Termination Fee": {
                "score": int(termination_fee_score),
                "value": f"${termination_fee:,.0f}" if termination_fee > 0 else "Not specified",
                "severity": cls._score_to_severity(termination_fee_score),
                "weight": "40%"
            },
            "Allowed Mileage": {
                "score": int(mileage_score),
                "value": f"{annual_mileage:,.0f} mi/year" if annual_mileage > 0 else "Not specified",
                "severity": cls._score_to_severity(mileage_score),
                "weight": "30%"
            },
            "Excess Mileage Fee": {
                "score": int(excess_fee_score),
                "value": f"${excess_fee:.2f}/mile" if excess_fee > 0 else "Not specified",
                "severity": cls._score_to_severity(excess_fee_score),
                "weight": "20%"
            },
            "Monthly Payment": {
                "score": int(monthly_payment_score),
                "value": f"${monthly_payment:,.0f}" if monthly_payment > 0 else "Not specified",
                "severity": cls._score_to_severity(monthly_payment_score),
                "weight": "5%"
            },
            "Interest Rate": {
                "score": int(interest_rate_score),
                "value": f"{interest_rate:.2f}%" if interest_rate > 0 else "Not specified",
                "severity": cls._score_to_severity(interest_rate_score),
                "weight": "5%"
            },
        }
        
        return {
            "status": "success",
            "risk_score": int(overall_score),
            "risk_level": risk_level,
            "breakdown": breakdown,
            "missing_fields": missing_fields,
            "notes": cls._generate_risk_notes(overall_score, breakdown, missing_fields)
        }
    
    @staticmethod
    def _score_to_severity(score: float) -> str:
        """Convert numeric score to severity label."""
        if score <= 25:
            return "Low"
        elif score <= 50:
            return "Medium"
        elif score <= 75:
            return "High"
        else:
            return "Critical"
    
    @staticmethod
    def _generate_risk_notes(overall_score: int, breakdown: Dict, missing_fields: list) -> str:
        """Generate human-readable risk interpretation."""
        
        notes = []
        
        if overall_score <= 25:
            notes.append("✓ Low Risk - This lease appears to have favorable terms.")
        elif overall_score <= 50:
            notes.append("⚠ Medium Risk - This lease is moderately risky. Review highlighted factors before committing.")
        elif overall_score <= 75:
            notes.append("⚠ High Risk - This lease carries significant risk. Carefully negotiate the highlighted terms.")
        else:
            notes.append("⚠ Critical Risk - This lease is very risky. Consider negotiating major terms or walking away.")
        
        # Add specific warnings
        warnings = []
        
        if breakdown["Early Termination Fee"]["score"] > 75:
            warnings.append("High early termination fee - Breaking the lease will be very expensive")
        elif breakdown["Early Termination Fee"]["score"] > 50:
            warnings.append("High early termination fee - Be cautious about breaking the lease early")
        
        if breakdown["Allowed Mileage"]["score"] > 75:
            warnings.append("Very low mileage allowance - Risky if you drive more than expected")
        elif breakdown["Allowed Mileage"]["score"] > 50:
            warnings.append("Limited mileage allowance - Track your driving to avoid overage penalties")
        
        if breakdown["Excess Mileage Fee"]["score"] > 75:
            warnings.append("Very high per-mile overage charges - Excess mileage will be very costly")
        elif breakdown["Excess Mileage Fee"]["score"] > 50:
            warnings.append("Significant per-mile overage charges - Manage mileage carefully")
        
        if breakdown["Monthly Payment"]["score"] > 50:
            warnings.append("High monthly payment - Ensure it fits your budget comfortably")
        
        if missing_fields:
            warnings.append(f"Missing critical terms: {', '.join(missing_fields)} - Get clarification before signing")
        
        if not warnings:
            warnings.append("✓ No major red flags detected in this lease's key terms")
        
        notes.extend(warnings)
        
        # Join with newlines for display
        return "\n".join(notes)
