# def generate_response(sla_data, risk_report):
#     print("\n========== CONTRACT SUMMARY ==========\n")

#     print(f"APR: {sla_data.get('apr', 'Not Found')}")
#     print(f"Term: {sla_data.get('term', 'Not Found')}")
#     print(f"Monthly Payment: {sla_data.get('monthly_payment', 'Not Found')}")
#     print(f"Down Payment: {sla_data.get('down_payment', 'Not Found')}")
#     print(f"Mileage Limit: {sla_data.get('mileage_limit', 'Not Found')}")

#     print("\n========== RISK REPORT ==========\n")
#     if risk_report:
#         for risk in risk_report:
#             print(f"- {risk}")
#     else:
#         print("No major risks detected.")



def generate_response(sla_data, risk_report):
    print("\n========== CONTRACT SUMMARY ==========\n")

    print(f"APR: {sla_data.get('interest_rate_apr', 'Not Found')}")
    print(f"Lease Term (months): {sla_data.get('lease_term_months', 'Not Found')}")
    print(f"Monthly Payment: {sla_data.get('monthly_payment', 'Not Found')}")
    print(f"Down Payment: {sla_data.get('down_payment', 'Not Found')}")
    print(f"Mileage Allowance: {sla_data.get('mileage_allowance', 'Not Found')}")
    print(f"Residual Value: {sla_data.get('residual_value', 'Not Found')}")
    print(f"Overage Charges: {sla_data.get('overage_charges', 'Not Found')}")
    print(f"Early Termination: {sla_data.get('early_termination_clause', 'Not Found')}")
    print(f"Buyout Price: {sla_data.get('purchase_option_buyout_price', 'Not Found')}")
    print(f"Maintenance: {sla_data.get('maintenance_responsibilities', 'Not Found')}")
    print(f"Warranty & Insurance: {sla_data.get('warranty_and_insurance', 'Not Found')}")
    print(f"Penalties / Late Fees: {sla_data.get('penalties_or_late_fees', 'Not Found')}")
    print(f"Fairness Score: {sla_data.get('contract_fairness_score', 'Not Found')}")

    print("\n========== RED FLAGS ==========\n")
    red_flags = sla_data.get("red_flags", [])
    if red_flags:
        for flag in red_flags:
            print(f"- {flag}")
    else:
        print("No red flags detected.")

    print("\n========== RISK REPORT ==========\n")
    if risk_report:
        for risk in risk_report:
            print(f"- {risk}")
    else:
        print("No major risks detected.")