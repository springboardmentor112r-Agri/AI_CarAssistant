import json

def risk_analysis(sla_data: dict) -> dict:
    """
    Generate risk analysis from SLA / contract data.

    Returns:
        {
            "risks": [
                {"level": "high/medium/low", "message": str}
            ],
            "contract_fairness_score": int (0-100)
        }
    """

    risks = []

    # ---------------------------
    # Financial term checks
    # ---------------------------
    financial = sla_data.get("Financial Terms", {})
    apr = financial.get("interest_rate_apr")

    if apr is not None:
        try:
            apr = float(apr)
            if apr > 8:
                risks.append({
                    "level": "high",
                    "message": f"High APR detected: {apr}%"
                })
            elif apr > 6:
                risks.append({
                    "level": "medium",
                    "message": f"Moderate APR: {apr}%"
                })
        except:
            risks.append({
                "level": "low",
                "message": f"Invalid APR format: {apr}"
            })

    # ---------------------------
    # Usage term checks
    # ---------------------------
    usage = sla_data.get("Usage Terms", {})
    mileage = usage.get("mileage_allowance")

    if mileage:
        try:
            mileage_int = int(str(mileage).replace(",", "").split()[0])
            if mileage_int < 10000:
                risks.append({
                    "level": "high",
                    "message": f"Low mileage allowance: {mileage_int} miles/year"
                })
            elif mileage_int < 12000:
                risks.append({
                    "level": "medium",
                    "message": f"Moderate mileage limit: {mileage_int} miles/year"
                })
        except:
            risks.append({
                "level": "low",
                "message": f"Invalid mileage format: {mileage}"
            })

    # ---------------------------
    # Contract condition checks
    # ---------------------------
    conditions = sla_data.get("Contract Conditions", {})

    # Early termination
    early_term = conditions.get("early_termination_clause")
    if isinstance(early_term, dict):
        fee = early_term.get("fee")
        if fee:
            risks.append({
                "level": "high",
                "message": f"Early termination fee: ${fee}"
            })
        for cond in early_term.get("conditions", []):
            risks.append({
                "level": "low",
                "message": f"Termination condition: {cond}"
            })
    elif isinstance(early_term, str):
        risks.append({
            "level": "low",
            "message": f"Termination clause: {early_term}"
        })

    # Maintenance
    maintenance = conditions.get("maintenance_responsibilities")
    if isinstance(maintenance, list):
        for item in maintenance:
            risks.append({
                "level": "low",
                "message": f"Maintenance responsibility: {item}"
            })
    elif isinstance(maintenance, str):
        risks.append({
            "level": "low",
            "message": f"Maintenance responsibility: {maintenance}"
        })

    # Insurance
    warranty = conditions.get("warranty_and_insurance")
    if isinstance(warranty, dict):
        for req in warranty.get("insurance_requirements", []):
            risks.append({
                "level": "medium",
                "message": f"Insurance requirement: {req}"
            })
    elif isinstance(warranty, str):
        risks.append({
            "level": "medium",
            "message": f"Insurance requirement: {warranty}"
        })

    # Penalties
    penalties = conditions.get("penalties_or_late_fees")
    if isinstance(penalties, dict):
        late_fee = penalties.get("late_payment_fee")
        if late_fee:
            risks.append({
                "level": "high",
                "message": f"Late payment fee: ${late_fee}"
            })
        additional_interest = penalties.get("additional_interest")
        if additional_interest:
            risks.append({
                "level": "high",
                "message": f"Additional interest: {additional_interest}%"
            })
    elif isinstance(penalties, str):
        risks.append({
            "level": "medium",
            "message": f"Penalties: {penalties}"
        })

    # ---------------------------
    # Fairness score
    # ---------------------------
    score = 100

    for r in risks:
        if r["level"] == "high":
            score -= 12
        elif r["level"] == "medium":
            score -= 7
        else:
            score -= 3

    score = max(0, score)

    return {
        "risks": risks,
        "contract_fairness_score": score
    }


# ---------------------------
# Example test
# ---------------------------
if __name__ == "__main__":
    test_contract = {
        "Financial Terms": {"interest_rate_apr": 9.5},
        "Usage Terms": {"mileage_allowance": "8,000 miles/year"},
        "Contract Conditions": {
            "penalties_or_late_fees": {
                "late_payment_fee": 150,
                "additional_interest": 2
            }
        }
    }

    result = risk_analysis(test_contract)
    print(json.dumps(result, indent=2))