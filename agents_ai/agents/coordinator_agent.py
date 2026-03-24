# from agents.preprocessing_agent import preprocess_text
# from agents.sla_extraction_agent import extract_sla
# from agents.validation_agent import validate_sla_data
# from agents.risk_analysis_agent import risk_analysis


# from agents.Vin import extract_vin, fetch_vehicle_data

# def process_contract(raw_text):

#     cleaned_text = preprocess_text(raw_text)

#     sla_data = extract_sla(cleaned_text)

#     validation_issues = validate_sla_data(sla_data)

#     risk_report = risk_analysis(sla_data)

#     # VIN handling
#     vin = extract_vin(cleaned_text)
#     vehicle_data = {}

#     if vin:
#         vehicle_data = fetch_vehicle_data(vin)

#     return {
#         "sla_data": sla_data,
#         "validation_issues": validation_issues,
#         "risk_report": risk_report,
#         "vin": vin,
#         "vehicle_data": vehicle_data
#     }








from agents.preprocessing_agent import preprocess_text
from agents.sla_extraction_agent import extract_sla
from agents.validation_agent import validate_sla_data
from agents.risk_analysis_agent import risk_analysis
from agents.Vin import extract_vin, fetch_vehicle_data


def chunk_text(text, max_chars=3000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]


def merge_sla_data(sla_list):
    merged = {}

    for sla in sla_list:
        if not isinstance(sla, dict):
            continue
        for key, value in sla.items():
            if key not in merged or merged[key] in [None, [], ""]:
                merged[key] = value

    return merged


def process_contract(raw_text):

    cleaned_text = preprocess_text(raw_text)

    chunks = chunk_text(cleaned_text)

    sla_results = []

    for chunk in chunks:
        sla = extract_sla(chunk)
        if isinstance(sla, dict):
            sla_results.append(sla)

    final_sla_data = merge_sla_data(sla_results)

    validation_issues = validate_sla_data(final_sla_data)

    risk_report = risk_analysis(final_sla_data)

    # VIN handling
    vin = extract_vin(cleaned_text)
    vehicle_data = {}

    if vin:
        vehicle_data = fetch_vehicle_data(vin)

    return {
        "sla_data": final_sla_data,
        "validation_issues": validation_issues,
        "risk_report": risk_report,
        "vin": vin,
        "vehicle_data": vehicle_data
    }