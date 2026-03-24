def validate_sla_data(sla_data):
    issues = []

    required_fields = ["apr", "term_months", "monthly_payment"]

    for field in required_fields:
        if field not in sla_data or sla_data[field] is None:
            issues.append(f"Missing value for {field}")

    return issues



