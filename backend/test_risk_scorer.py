#!/usr/bin/env python3
"""
Quick test of the LeaseRiskScorer functionality
"""

from risk_scorer import LeaseRiskScorer
import json

# Test with a moderate risk lease
sample_lease_medium = {
    "Agreement Number": "TEST-001",
    "Allowed Mileage": "36000",  # 12k per year for 36 months
    "Excess Mileage Fee": "0.25",  # $0.25 per mile
    "Early Termination Fee": "5000",  # $5000
    "Monthly Payment": "450",  # $450/month
    "Interest Rate": "4.5"  # 4.5%
}

print("=" * 70)
print("TEST: Medium Risk Lease")
print("=" * 70)
result = LeaseRiskScorer.calculate_lease_risk(sample_lease_medium)
print(json.dumps(result, indent=2))

# Test with a high risk lease
sample_lease_high = {
    "Agreement Number": "TEST-002",
    "Allowed Mileage": "20000",  # 6.67k per year (very low!)
    "Excess Mileage Fee": "0.50",  # $0.50 per mile (very high!)
    "Early Termination Fee": "10000",  # $10000 (very high!)
    "Monthly Payment": "700",  # $700/month
    "Interest Rate": "8.5"  # 8.5%
}

print("\n" + "=" * 70)
print("TEST: High Risk Lease")
print("=" * 70)
result = LeaseRiskScorer.calculate_lease_risk(sample_lease_high)
print(json.dumps(result, indent=2))

# Test with missing fields
sample_lease_missing = {
    "Agreement Number": "TEST-003",
    "Allowed Mileage": None,  # Missing!
    "Excess Mileage Fee": "0.20",
    "Early Termination Fee": None,  # Missing!
    "Monthly Payment": None,  # Missing!
    "Interest Rate": None
}

print("\n" + "=" * 70)
print("TEST: Lease with Missing Fields")
print("=" * 70)
result = LeaseRiskScorer.calculate_lease_risk(sample_lease_missing)
print(json.dumps(result, indent=2))

# Test with low risk lease
sample_lease_low = {
    "Agreement Number": "TEST-004",
    "Allowed Mileage": "120000",  # 10k per year
    "Excess Mileage Fee": "0.10",  # $0.10 per mile
    "Early Termination Fee": "1500",  # $1500
    "Monthly Payment": "300",  # $300/month
    "Interest Rate": "2.5"  # 2.5%
}

print("\n" + "=" * 70)
print("TEST: Low Risk Lease")
print("=" * 70)
result = LeaseRiskScorer.calculate_lease_risk(sample_lease_low)
print(json.dumps(result, indent=2))

print("\n" + "=" * 70)
print("All tests completed successfully!")
print("=" * 70)
