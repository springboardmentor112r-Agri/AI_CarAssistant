def analyze_risk(contract_data):

    risks = []
    score = 100

    down_payment = contract_data.get("Down_Payment")
    if down_payment:
        down_payment = int(down_payment)

        if down_payment > 5000:
            risks.append("Very high down payment")
            score -= 20
        elif down_payment > 3000:
            risks.append("High down payment")
            score -= 10

    term = contract_data.get("Loan_Term_Months")
    if term:
        term = int(term)

        if term > 60:
            risks.append("Extremely long lease term")
            score -= 20
        elif term > 48:
            risks.append("Long lease term (>48 months)")
            score -= 10

    mileage = contract_data.get("Mileage_Limit")
    if mileage:
        mileage = int(mileage)

        if mileage < 10000:
            risks.append("Very low mileage allowance")
            score -= 20
        elif mileage < 12000:
            risks.append("Low mileage allowance")
            score -= 10

    termination = contract_data.get("Termination_Fee")
    if termination:
        termination = int(termination)

        if termination > 2000:
            risks.append("Very high early termination fee")
            score -= 15
        elif termination > 1000:
            risks.append("High early termination fee")
            score -= 10

    if score >= 80:
        level = "LOW"
    elif score >= 60:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "risks": risks,
        "score": score,
        "level": level
    }
