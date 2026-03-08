def suggest_negotiation_points(contract_data):

    suggestions = []

    down = contract_data.get("Down_Payment")
    if down and int(down) > 3000:
        suggestions.append("Try negotiating a lower down payment (below $3000).")

    term = contract_data.get("Loan_Term_Months")
    if term and int(term) > 48:
        suggestions.append("Request a shorter lease term (36–48 months).")

    mileage = contract_data.get("Mileage_Limit")
    if mileage and int(mileage) < 12000:
        suggestions.append("Ask for a higher mileage allowance (15,000 per year).")

    termination = contract_data.get("Termination_Fee")
    if termination and int(termination) > 1000:
        suggestions.append("Negotiate a lower early termination fee.")

    return suggestions
