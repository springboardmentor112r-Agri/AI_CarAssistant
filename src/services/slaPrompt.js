/**
 * SLA Extraction Prompt Template for Car Lease Contracts
 * 
 * This prompt is designed to extract structured SLA (Service Level Agreement)
 * details from car lease documents using Amazon Nova 2 Lite via OpenRouter.
 */

export const SLA_EXTRACTION_SYSTEM_PROMPT = `You are an expert car lease contract analyst specializing in extracting Service Level Agreement (SLA) details from vehicle lease documents.

Your task is to analyze car lease documents and extract ALL relevant SLA details into a precise, structured JSON format.

IMPORTANT RULES:
1. Return ONLY a valid JSON object — no markdown formatting, no code blocks, no explanatory text.
2. If a field's value cannot be found in the document, use "Not specified" as the value.
3. Extract exact values, amounts ($), dates, percentages (%), and mileage figures as written in the document.
4. For monetary values, include the currency symbol and exact amount (e.g., "$389.00").
5. For dates, use the format found in the document or ISO format (YYYY-MM-DD).
6. For the additional_terms array, include any important clauses not covered by the main fields.
7. Be thorough — do not skip any SLA-relevant information.

Return the JSON in this exact structure:
{
  "document_info": {
    "document_type": "Type of lease document",
    "document_date": "Date the contract was created/signed",
    "contract_number": "Contract or agreement reference number"
  },
  "parties": {
    "lessor": {
      "name": "Leasing company or dealer name",
      "address": "Full address of lessor",
      "contact": "Phone, email, or other contact info"
    },
    "lessee": {
      "name": "Customer/lessee full name",
      "address": "Full address of lessee",
      "contact": "Phone, email, or other contact info",
      "license_number": "Driver license number"
    }
  },
  "vehicle_details": {
    "make": "Vehicle manufacturer",
    "model": "Vehicle model and trim",
    "year": "Model year",
    "vin": "Vehicle Identification Number",
    "color": "Exterior color",
    "mileage_at_start": "Odometer reading at lease start"
  },
  "lease_terms": {
    "start_date": "Lease commencement date",
    "end_date": "Lease termination date",
    "duration_months": "Total lease period in months",
    "monthly_payment": "Monthly installment amount",
    "down_payment": "Initial down payment / capitalized cost reduction",
    "security_deposit": "Refundable security deposit amount",
    "total_lease_cost": "Total financial obligation over lease term"
  },
  "mileage_terms": {
    "annual_mileage_limit": "Permitted miles per year",
    "total_mileage_limit": "Total permitted miles over lease term",
    "excess_mileage_charge_per_mile": "Cost per mile over the limit"
  },
  "sla_obligations": {
    "maintenance_responsibility": "Who is responsible for maintenance and what it covers",
    "insurance_requirements": "Required insurance coverage types and minimum limits",
    "wear_and_tear_policy": "Acceptable vs excessive wear and tear definitions",
    "service_schedule": "Required service intervals and inspections"
  },
  "penalties": {
    "late_payment_fee": "Fee for late payments, grace period, and interest rates",
    "early_termination_fee": "Penalty for ending lease early",
    "excess_wear_charges": "Charges for damage beyond normal wear",
    "missing_equipment_charges": "Charges for missing keys, manuals, equipment"
  },
  "end_of_lease_options": {
    "purchase_option": "Option to buy vehicle at lease end and any associated fees",
    "residual_value": "Predetermined residual/buyout value of the vehicle",
    "return_conditions": "Requirements for returning the vehicle"
  },
  "additional_terms": ["Array of any other important SLA terms, clauses, or conditions"]
}`;

export const SLA_IMAGE_USER_PROMPT = `Analyze this car lease document image and extract ALL SLA (Service Level Agreement) details into the structured JSON format specified. Be thorough and precise.`;

export const SLA_TEXT_USER_PROMPT = (text) =>
  `Extract all SLA (Service Level Agreement) details from the following car lease document text into the structured JSON format specified. Be thorough and precise.\n\n--- DOCUMENT TEXT ---\n${text}\n--- END DOCUMENT ---`;

/**
 * Empty SLA template for reference/validation
 */
export const EMPTY_SLA_TEMPLATE = {
  document_info: {
    document_type: "Not specified",
    document_date: "Not specified",
    contract_number: "Not specified",
  },
  parties: {
    lessor: { name: "Not specified", address: "Not specified", contact: "Not specified" },
    lessee: { name: "Not specified", address: "Not specified", contact: "Not specified", license_number: "Not specified" },
  },
  vehicle_details: {
    make: "Not specified",
    model: "Not specified",
    year: "Not specified",
    vin: "Not specified",
    color: "Not specified",
    mileage_at_start: "Not specified",
  },
  lease_terms: {
    start_date: "Not specified",
    end_date: "Not specified",
    duration_months: "Not specified",
    monthly_payment: "Not specified",
    down_payment: "Not specified",
    security_deposit: "Not specified",
    total_lease_cost: "Not specified",
  },
  mileage_terms: {
    annual_mileage_limit: "Not specified",
    total_mileage_limit: "Not specified",
    excess_mileage_charge_per_mile: "Not specified",
  },
  sla_obligations: {
    maintenance_responsibility: "Not specified",
    insurance_requirements: "Not specified",
    wear_and_tear_policy: "Not specified",
    service_schedule: "Not specified",
  },
  penalties: {
    late_payment_fee: "Not specified",
    early_termination_fee: "Not specified",
    excess_wear_charges: "Not specified",
    missing_equipment_charges: "Not specified",
  },
  end_of_lease_options: {
    purchase_option: "Not specified",
    residual_value: "Not specified",
    return_conditions: "Not specified",
  },
  additional_terms: [],
};
