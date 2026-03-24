# from agents.document_handler_agent import extract_text_from_file
# from agents.coordinator_agent import process_contract
# from agents.summary_agent import generate_response


# def main():
#     pdf_path = "./uploads/VEHICLE-LOAN-Agreement.pdf"

#     # Extract text from PDF
#     raw_text = extract_text_from_file(pdf_path)

#     print("\n========== FULL EXTRACTED TEXT ==========\n")
#     print(raw_text)

#     # Safely process contract
#     result = process_contract(raw_text)

#     # Handle both dict and tuple/list returns
#     if isinstance(result, dict):
#         sla_data = result.get("sla_data")
#         validation_issues = result.get("validation_issues")
#         risk_report = result.get("risk_report")
#     elif isinstance(result, (tuple, list)):
#         # Unpack first 3 elements safely, ignore extras
#         sla_data, validation_issues, risk_report, *rest = result
#     else:
#         raise TypeError(f"Unexpected return type from process_contract: {type(result)}")

#     # Show validation issues if any
#     if validation_issues:
#         print("\nValidation Issues:", validation_issues)
#         print("Cannot generate full summary due to missing fields.\n")

#     # Generate summary
#     generate_response(sla_data, risk_report)


# if __name__ == "__main__":
#     main()


from agents.document_handler_agent import extract_text_from_file
from agents.coordinator_agent import process_contract
from agents.summary_agent import generate_response


def chunk_text(text, max_chars=3000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]


def run_contract_pipeline(file_path):

    # Extract text
    raw_text = extract_text_from_file(file_path)

    chunks = chunk_text(raw_text)

    all_sla_data = []
    all_validation_issues = []
    all_risk_reports = []

    for chunk in chunks:

        result = process_contract(chunk)

        if isinstance(result, dict):

            sla_data = result.get("sla_data")
            validation_issues = result.get("validation_issues")
            risk_report = result.get("risk_report")

        elif isinstance(result, (tuple, list)):

            sla_data, validation_issues, risk_report, *rest = result

        else:
            raise TypeError(
                f"Unexpected return type from process_contract: {type(result)}"
            )

        if sla_data:
            all_sla_data.append(sla_data)

        if validation_issues:
            all_validation_issues.extend(validation_issues)

        if risk_report:
            all_risk_reports.extend(risk_report)

    summary = generate_response(all_sla_data, all_risk_reports)

    # Return structured JSON for frontend
    return {
        "sla_data": all_sla_data,
        "validation_issues": all_validation_issues,
        "risk_report": all_risk_reports,
        "summary": summary
    }