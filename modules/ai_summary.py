def generate_summary(contract_data, vehicle_info, risks):

    down_payment = contract_data.get("Down_Payment", "unknown")
    monthly_payment = contract_data.get("Monthly_Payment", "unknown")
    term = contract_data.get("Loan_Term_Months", "unknown")

    make = vehicle_info.get("Make", "")
    model = vehicle_info.get("Model", "")
    year = vehicle_info.get("Model_Year", "")

    summary = f"""
This lease agreement is for a {year} {make} {model}.

The contract requires a down payment of ${down_payment} and monthly payments of ${monthly_payment} over {term} months.
"""

    if len(risks) == 0:
        summary += "\nNo major financial risks were detected."
    else:
        summary += "\nThe system detected the following risks:\n"
        for r in risks:
            summary += f"- {r}\n"

    return summary
