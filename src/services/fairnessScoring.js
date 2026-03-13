/**
 * Fairness scoring and red flag detection for car lease contracts.
 * Compares extracted SLA data against market averages and recommended thresholds.
 */

// ─── Thresholds ──────────────────────────────────────────────────
const THRESHOLDS = {
  interestRate: 8,               // APR %
  mileageLimitPerYear: 10000,    // miles/year
  earlyTerminationFee: 1000,     // $
  adminFee: 500,                 // $
  leaseTermMonths: 60,           // months
  downPaymentRatio: 0.30,        // 30% of vehicle value
};

// ─── Helpers ─────────────────────────────────────────────────────

/** Extract a numeric value from a string like "$450/month", "6.5%", "36 months", etc. */
function parseNumeric(value) {
  if (value == null) return NaN;
  if (typeof value === 'number') return value;
  const cleaned = String(value).replace(/[,$%]/g, '').trim();
  const match = cleaned.match(/([\d.]+)/);
  return match ? parseFloat(match[1]) : NaN;
}

/** Check if a string contains a dollar amount and return it */
function parseDollar(value) {
  return parseNumeric(value);
}

/** Determine if a value looks like it mentions "per year" or "annual" */
function isAnnualMileage(value) {
  if (typeof value !== 'string') return true; // assume annual if just a number
  return /year|annual|yr|p\.a/i.test(value);
}

// ─── Red Flag Detection ─────────────────────────────────────────

export function detectRedFlags(slaData) {
  const flags = [];
  if (!slaData) return flags;

  const lease = slaData.lease_terms || {};
  const mileage = slaData.mileage_terms || {};
  const penalties = slaData.penalties || {};
  const endOfLease = slaData.end_of_lease_options || {};

  // 1. Interest rate > 8%
  const apr = parseNumeric(lease.interest_rate || lease.apr);
  if (!isNaN(apr) && apr > THRESHOLDS.interestRate) {
    flags.push({
      type: 'High Interest Rate',
      severity: apr > 15 ? 'high' : apr > 10 ? 'medium' : 'low',
      description: `Interest rate of ${apr}% exceeds the ${THRESHOLDS.interestRate}% threshold.`,
      recommendation: 'Negotiate a lower APR or shop around for better financing options.',
    });
  }

  // 2. Mileage limit < 10,000 miles/year
  const annualMileage = parseNumeric(mileage.annual_mileage_limit);
  if (!isNaN(annualMileage) && annualMileage < THRESHOLDS.mileageLimitPerYear) {
    flags.push({
      type: 'Low Mileage Limit',
      severity: annualMileage < 7500 ? 'high' : 'medium',
      description: `Annual mileage limit of ${annualMileage.toLocaleString()} miles is below the recommended ${THRESHOLDS.mileageLimitPerYear.toLocaleString()} miles/year.`,
      recommendation: 'Negotiate a higher mileage allowance or confirm excess mileage fees are reasonable.',
    });
  }

  // 3. Early termination fee > $1,000
  const earlyTermFee = parseDollar(penalties.early_termination_fee);
  if (!isNaN(earlyTermFee) && earlyTermFee > THRESHOLDS.earlyTerminationFee) {
    flags.push({
      type: 'High Early Termination Fee',
      severity: earlyTermFee > 2000 ? 'high' : 'medium',
      description: `Early termination fee of $${earlyTermFee.toLocaleString()} exceeds the $${THRESHOLDS.earlyTerminationFee.toLocaleString()} threshold.`,
      recommendation: 'Negotiate a lower early exit penalty or ensure you can commit to the full lease term.',
    });
  }

  // 4. Processing / admin fees > $500
  const additionalTerms = slaData.additional_terms || [];
  for (const term of additionalTerms) {
    const termStr = typeof term === 'string' ? term : JSON.stringify(term);
    const feeMatch = termStr.match(/(?:processing|admin|administrative|documentation)\s*fee[^$]*\$\s*([\d,.]+)/i);
    if (feeMatch) {
      const fee = parseFloat(feeMatch[1].replace(/,/g, ''));
      if (fee > THRESHOLDS.adminFee) {
        flags.push({
          type: 'High Administrative Fee',
          severity: fee > 1000 ? 'high' : 'medium',
          description: `Administrative/processing fee of $${fee.toLocaleString()} exceeds $${THRESHOLDS.adminFee} threshold.`,
          recommendation: 'Ask for a fee reduction or waiver — these are often negotiable.',
        });
      }
    }
  }

  // 5. Lease term > 60 months
  const duration = parseNumeric(lease.duration_months);
  if (!isNaN(duration) && duration > THRESHOLDS.leaseTermMonths) {
    flags.push({
      type: 'Long Lease Term',
      severity: duration > 72 ? 'high' : 'medium',
      description: `Lease term of ${duration} months exceeds the recommended ${THRESHOLDS.leaseTermMonths}-month maximum.`,
      recommendation: 'Consider a shorter lease to avoid paying more in depreciation and potential out-of-warranty repairs.',
    });
  }

  // 6. Down payment > 30% of vehicle value
  const downPayment = parseDollar(lease.down_payment);
  const totalCost = parseDollar(lease.total_lease_cost);
  const monthlyPayment = parseDollar(lease.monthly_payment);
  let estimatedVehicleValue = NaN;

  // Try to estimate vehicle value from residual + total cost
  const residual = parseDollar(endOfLease.residual_value);
  if (!isNaN(totalCost)) estimatedVehicleValue = totalCost;
  else if (!isNaN(monthlyPayment) && !isNaN(duration)) estimatedVehicleValue = monthlyPayment * duration;

  if (!isNaN(downPayment) && !isNaN(estimatedVehicleValue) && estimatedVehicleValue > 0) {
    const ratio = downPayment / estimatedVehicleValue;
    if (ratio > THRESHOLDS.downPaymentRatio) {
      flags.push({
        type: 'High Down Payment',
        severity: ratio > 0.5 ? 'high' : 'medium',
        description: `Down payment of $${downPayment.toLocaleString()} is ${(ratio * 100).toFixed(0)}% of calculated lease value.`,
        recommendation: 'Consider negotiating the down payment below 30% to reduce upfront financial risk.',
      });
    }
  }

  // 7. Monthly payment significantly higher than market range
  // Market estimate: ~$300-$500/month for average car lease
  if (!isNaN(monthlyPayment) && monthlyPayment > 700) {
    flags.push({
      type: 'High Monthly Payment',
      severity: monthlyPayment > 1000 ? 'high' : monthlyPayment > 800 ? 'medium' : 'low',
      description: `Monthly payment of $${monthlyPayment.toLocaleString()} is above the typical $300–$500 market range for standard leases.`,
      recommendation: 'Compare with other dealerships and online lease calculators to verify competitiveness.',
    });
  }

  // 8. No purchase option mentioned
  const purchaseOption = endOfLease.purchase_option;
  if (!purchaseOption || purchaseOption === 'Not specified' || purchaseOption === 'N/A') {
    flags.push({
      type: 'No Purchase Option',
      severity: 'low',
      description: 'The contract does not specify an end-of-lease purchase option.',
      recommendation: 'Ask for a guaranteed purchase price at lease end for more flexibility.',
    });
  }

  return flags;
}

// ─── Fairness Score Calculation ──────────────────────────────────

export function calculateFairnessScore(slaData) {
  if (!slaData) return { score: 0, breakdown: [], rating: 'Unknown' };

  const lease = slaData.lease_terms || {};
  const mileage = slaData.mileage_terms || {};
  const penalties = slaData.penalties || {};
  const endOfLease = slaData.end_of_lease_options || {};

  const breakdown = [];
  let totalWeight = 0;
  let weightedScore = 0;

  // Helper: add a scored criterion
  function addCriterion(name, weight, rawValue, scoreFn) {
    const val = parseNumeric(rawValue);
    if (isNaN(val)) {
      // Cannot evaluate — skip but note it
      breakdown.push({ name, weight, value: 'N/A', score: null, note: 'Not found in contract' });
      return;
    }
    const score = Math.max(0, Math.min(100, scoreFn(val)));
    breakdown.push({ name, weight, value: rawValue, score });
    totalWeight += weight;
    weightedScore += score * weight;
  }

  // 1. Interest rate (weight: 20)
  addCriterion('Interest Rate', 20, lease.interest_rate || lease.apr, (apr) => {
    if (apr <= 3) return 100;
    if (apr <= 5) return 85;
    if (apr <= 8) return 65;
    if (apr <= 12) return 35;
    return 10;
  });

  // 2. Monthly payment (weight: 20)
  addCriterion('Monthly Payment', 20, lease.monthly_payment, (pmt) => {
    if (pmt <= 250) return 100;
    if (pmt <= 400) return 85;
    if (pmt <= 600) return 65;
    if (pmt <= 800) return 40;
    return 20;
  });

  // 3. Lease duration (weight: 15)
  addCriterion('Lease Duration', 15, lease.duration_months, (months) => {
    if (months <= 24) return 90;
    if (months <= 36) return 100;
    if (months <= 48) return 75;
    if (months <= 60) return 50;
    return 20;
  });

  // 4. Annual mileage limit (weight: 15)
  addCriterion('Mileage Limit', 15, mileage.annual_mileage_limit, (miles) => {
    if (miles >= 15000) return 100;
    if (miles >= 12000) return 85;
    if (miles >= 10000) return 65;
    if (miles >= 7500) return 35;
    return 10;
  });

  // 5. Early termination fee (weight: 10)
  addCriterion('Early Termination Fee', 10, penalties.early_termination_fee, (fee) => {
    if (fee <= 200) return 100;
    if (fee <= 500) return 80;
    if (fee <= 1000) return 55;
    if (fee <= 2000) return 30;
    return 10;
  });

  // 6. Down payment (weight: 10)
  addCriterion('Down Payment', 10, lease.down_payment, (dp) => {
    if (dp <= 1000) return 100;
    if (dp <= 2500) return 80;
    if (dp <= 5000) return 55;
    if (dp <= 8000) return 35;
    return 15;
  });

  // 7. Residual value (weight: 10)
  addCriterion('Residual Value', 10, endOfLease.residual_value, (rv) => {
    // Higher residual = better (lower depreciation cost)
    if (rv >= 25000) return 90;
    if (rv >= 18000) return 75;
    if (rv >= 12000) return 60;
    if (rv >= 8000) return 40;
    return 25;
  });

  // Calculate final score
  const score = totalWeight > 0 ? Math.round(weightedScore / totalWeight) : 0;

  let rating;
  if (score >= 80) rating = 'Excellent';
  else if (score >= 60) rating = 'Fair';
  else if (score >= 40) rating = 'Needs Negotiation';
  else rating = 'Poor';

  return { score, breakdown, rating };
}

// ─── Combined Analysis ───────────────────────────────────────────

export function analyzeContract(slaData) {
  const { score, breakdown, rating } = calculateFairnessScore(slaData);
  const redFlags = detectRedFlags(slaData);
  return { score, breakdown, rating, redFlags };
}

// ─── Market-Aware Scoring ────────────────────────────────────────

/**
 * Score a single metric against a market range.
 * Returns 0–100. 
 *   - Values at or better than market avg → 80–100
 *   - Values between avg and high → 50–80
 *   - Values above high → 10–50
 * "lowerIsBetter" means a lower contract value is better (e.g. monthly payment, APR).
 */
function scoreAgainstMarket(value, range, lowerIsBetter = true) {
  if (isNaN(value) || !range) return null;
  const { low, avg, high } = range;

  if (lowerIsBetter) {
    if (value <= low) return 100;
    if (value <= avg) return 80 + 20 * ((avg - value) / (avg - low || 1));
    if (value <= high) return 50 + 30 * ((high - value) / (high - avg || 1));
    // Beyond high
    const overshoot = Math.min((value - high) / (high || 1), 1);
    return Math.max(5, Math.round(50 * (1 - overshoot)));
  } else {
    // Higher is better (e.g. residual value, mileage limit)
    if (value >= high) return 100;
    if (value >= avg) return 80 + 20 * ((value - avg) / (high - avg || 1));
    if (value >= low) return 50 + 30 * ((value - low) / (avg - low || 1));
    const undershoot = Math.min((low - value) / (low || 1), 1);
    return Math.max(5, Math.round(50 * (1 - undershoot)));
  }
}

/**
 * Build market comparison entries for display.
 */
export function buildMarketComparison(slaData, marketData) {
  if (!slaData || !marketData) return [];

  const lease = slaData.lease_terms || {};
  const mileage = slaData.mileage_terms || {};
  const penalties = slaData.penalties || {};
  const endOfLease = slaData.end_of_lease_options || {};

  const items = [];

  function addItem(label, rawValue, range, lowerIsBetter, prefix = '$') {
    const val = parseNumeric(rawValue);
    const score = scoreAgainstMarket(val, range, lowerIsBetter);
    const isPercent = prefix === '%';
    const fmt = (n) => {
      if (isNaN(n)) return 'N/A';
      return isPercent ? `${n}%` : `$${n.toLocaleString()}`;
    };
    items.push({
      label,
      contractValue: isNaN(val) ? 'N/A' : fmt(val),
      marketLow: fmt(range.low),
      marketAvg: fmt(range.avg),
      marketHigh: fmt(range.high),
      score,
      status: score === null ? 'unknown'
            : score >= 80 ? 'good'
            : score >= 50 ? 'fair'
            : 'poor',
    });
  }

  function addPlainItem(label, rawValue, range, lowerIsBetter) {
    const val = parseNumeric(rawValue);
    const score = scoreAgainstMarket(val, range, lowerIsBetter);
    const fmt = (n) => isNaN(n) ? 'N/A' : n.toLocaleString();
    items.push({
      label,
      contractValue: isNaN(val) ? 'N/A' : fmt(val),
      marketLow: fmt(range.low),
      marketAvg: fmt(range.avg),
      marketHigh: fmt(range.high),
      score,
      status: score === null ? 'unknown'
            : score >= 80 ? 'good'
            : score >= 50 ? 'fair'
            : 'poor',
    });
  }

  if (marketData.monthlyPayment)
    addItem('Monthly Payment', lease.monthly_payment, marketData.monthlyPayment, true);
  if (marketData.interestRate)
    addItem('Interest Rate', lease.interest_rate || lease.apr, marketData.interestRate, true, '%');
  if (marketData.residualValue)
    addItem('Residual Value', endOfLease.residual_value, marketData.residualValue, false);
  if (marketData.downPayment)
    addItem('Down Payment', lease.down_payment, marketData.downPayment, true);
  if (marketData.annualMileageLimit)
    addPlainItem('Annual Mileage', mileage.annual_mileage_limit, marketData.annualMileageLimit, false);
  if (marketData.leaseTerm)
    addPlainItem('Lease Term (months)', lease.duration_months, marketData.leaseTerm, true);
  if (marketData.earlyTerminationFee)
    addItem('Early Termination Fee', penalties.early_termination_fee, marketData.earlyTerminationFee, true);
  if (marketData.totalLeaseCost)
    addItem('Total Lease Cost', lease.total_lease_cost, marketData.totalLeaseCost, true);

  return items;
}

/**
 * Calculate an overall market-adjusted fairness score.
 */
export function calculateMarketScore(slaData, marketData) {
  const comparison = buildMarketComparison(slaData, marketData);
  const scored = comparison.filter(c => c.score !== null);
  if (scored.length === 0) return { score: 0, rating: 'Unknown', comparison };

  const avg = Math.round(scored.reduce((s, c) => s + c.score, 0) / scored.length);
  let rating;
  if (avg >= 80) rating = 'Excellent';
  else if (avg >= 60) rating = 'Fair';
  else if (avg >= 40) rating = 'Needs Negotiation';
  else rating = 'Poor';

  return { score: avg, rating, comparison };
}
