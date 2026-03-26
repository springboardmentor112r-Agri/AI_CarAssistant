import re

# 🔹 Extract number safely
def extract_number(value):
    try:
        value = str(value).replace(",", "")
        numbers = re.findall(r"\d+", value)
        return int(numbers[0]) if numbers else 0
    except:
        return 0


def calculate_fairness(data):

    score = 100
    red_flags = []

    # 🔹 Extract values
    monthly_payment = extract_number(data.get("monthly_payment"))
    down_payment = extract_number(data.get("down_payment"))
    mileage = extract_number(data.get("annual_mileage_limit"))
    duration = extract_number(data.get("lease_duration"))
    buyout = extract_number(data.get("purchase_option"))

    # ================================
    # 💰 1. Monthly Payment Analysis
    # ================================
    if monthly_payment > 70000:
        score -= 25
        red_flags.append("Very high monthly payment")
    elif monthly_payment > 50000:
        score -= 25
        red_flags.append("High monthly payment")
    elif monthly_payment > 30000:
        score -= 25

    elif monthly_payment == 0:
        red_flags.append("Monthly payment missing")

    # ================================
    # 💸 2. Down Payment Analysis
    # ================================
    if down_payment > 300000:
        score -= 20
        red_flags.append("Very high down payment")
    elif down_payment > 150000:
        score -= 20
        red_flags.append("High down payment")

    elif down_payment == 0:
        red_flags.append("No down payment info")

    # ================================
    # 🚗 3. Mileage Analysis
    # ================================
    if mileage < 8000:
        score -= 20
        red_flags.append("Very low mileage limit")
    elif mileage < 12000:
        score -= 20
        red_flags.append("Low mileage limit")

    elif mileage > 20000:
        score += 5  # bonus

    elif mileage == 0:
        red_flags.append("Mileage data missing")

    # ================================
    # ⏳ 4. Lease Duration Analysis
    # ================================
    if duration > 60:
        score -= 10
        red_flags.append("Too long lease duration")
    elif duration > 48:
        score -= 10

    elif duration < 24 and duration != 0:
        score += 5  # short lease is flexible

    elif duration == 0:
        red_flags.append("Lease duration missing")

    # ================================
    # 💎 5. Cost Consistency Check (NEW 🔥)
    # ================================
    if monthly_payment and duration:
        total_cost = monthly_payment * duration

        if buyout and buyout > total_cost:
            score -= 10
            red_flags.append("Buyout cost unusually high")

    # ================================
    # ⚠️ 6. Missing Critical Fields
    # ================================
    important_fields = ["monthly_payment", "down_payment", "annual_mileage_limit"]

    missing_count = 0
    for field in important_fields:
        if not data.get(field) or data.get(field) == "Not Found":
            missing_count += 1

    if missing_count >= 2:
        score -= 10
        red_flags.append("Incomplete contract data")

    # ================================
    # 🎯 FINAL SCORE ADJUSTMENT
    # ================================
    score = max(min(score, 100), 0)

    # ================================
    # 🚨 RISK CLASSIFICATION
    # ================================
    if score >= 80:
        risk = "SAFE"
    elif score >= 60:
        risk = "MEDIUM"
    else:
        risk = "DANGER"

    return {
        "score": score,
        "risk": risk,
        "red_flags": red_flags,
        "vin": data.get("vin_number", "Not Found")
    }