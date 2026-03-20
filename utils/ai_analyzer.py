import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def analyze_contract(contract_text):

    prompt = f"""
You are a contract analysis assistant.

Extract all important fields from this car lease or loan contract.

Return the result strictly in JSON format.
Do NOT include explanation or markdown.

Fields to extract:
document_type
document_date
contract_number

lessor_name
lessor_address
lessor_contact

lessee_name
lessee_address
lessee_contact
license_number

vehicle_make
vehicle_model
vehicle_year
vin_number
vehicle_color
starting_mileage

lease_start_date
lease_end_date
lease_duration
monthly_payment
down_payment
security_deposit
total_lease_cost

annual_mileage_limit
total_mileage_limit
excess_mileage_charge

maintenance
insurance_requirements
wear_and_tear_policy
service_schedule

late_payment_fee
early_termination_fee
excess_wear_charges
missing_equipment_charges

purchase_option
residual_value
return_conditions

additional_terms


If any field is missing return "Not Found".
Contract:
{contract_text}
"""

    try:

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile"
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        return "AI Processing Error: " + str(e)