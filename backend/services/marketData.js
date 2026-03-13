/**
 * Market Data Estimation Service
 *
 * Estimates fair-market lease values for vehicles based on make, model, and year.
 * Uses vehicle classification + MSRP estimation to produce expected ranges for
 * monthly payment, interest rate, residual value, mileage limits, and more.
 *
 * In production, swap the estimation logic with calls to Edmunds / KBB / TrueCar APIs.
 */

// ─── Vehicle Classification ─────────────────────────────────────

const VEHICLE_CLASSES = {
  economy:    { msrpRange: [18000, 25000], residualPct: 0.52, moneyFactor: 0.0015, typicalTerm: 36 },
  compact:    { msrpRange: [23000, 30000], residualPct: 0.54, moneyFactor: 0.0018, typicalTerm: 36 },
  midsize:    { msrpRange: [28000, 38000], residualPct: 0.50, moneyFactor: 0.0020, typicalTerm: 36 },
  fullsize:   { msrpRange: [35000, 50000], residualPct: 0.48, moneyFactor: 0.0022, typicalTerm: 36 },
  suv:        { msrpRange: [32000, 55000], residualPct: 0.53, moneyFactor: 0.0020, typicalTerm: 36 },
  luxury:     { msrpRange: [45000, 80000], residualPct: 0.50, moneyFactor: 0.0025, typicalTerm: 36 },
  luxury_suv: { msrpRange: [55000, 95000], residualPct: 0.51, moneyFactor: 0.0025, typicalTerm: 36 },
  truck:      { msrpRange: [35000, 65000], residualPct: 0.55, moneyFactor: 0.0018, typicalTerm: 36 },
  sports:     { msrpRange: [35000, 70000], residualPct: 0.48, moneyFactor: 0.0022, typicalTerm: 36 },
  electric:   { msrpRange: [35000, 80000], residualPct: 0.45, moneyFactor: 0.0016, typicalTerm: 36 },
  minivan:    { msrpRange: [30000, 45000], residualPct: 0.47, moneyFactor: 0.0020, typicalTerm: 36 },
};

// Make → { model → class } lookup (covers popular brands)
const MAKE_MODEL_MAP = {
  toyota:     { camry: 'midsize', corolla: 'compact', rav4: 'suv', highlander: 'suv', tacoma: 'truck', tundra: 'truck', prius: 'compact', sienna: 'minivan', '4runner': 'suv', supra: 'sports', 'land cruiser': 'luxury_suv', 'gr86': 'sports', 'bz4x': 'electric', venza: 'suv', avalon: 'fullsize', yaris: 'economy', _default: 'midsize' },
  honda:      { civic: 'compact', accord: 'midsize', 'cr-v': 'suv', 'hr-v': 'suv', pilot: 'suv', ridgeline: 'truck', odyssey: 'minivan', passport: 'suv', fit: 'economy', insight: 'compact', prologue: 'electric', _default: 'compact' },
  ford:       { mustang: 'sports', f150: 'truck', 'f-150': 'truck', explorer: 'suv', escape: 'suv', bronco: 'suv', ranger: 'truck', edge: 'suv', fusion: 'midsize', focus: 'compact', expedition: 'luxury_suv', 'mustang mach-e': 'electric', maverick: 'truck', _default: 'midsize' },
  chevrolet:  { malibu: 'midsize', equinox: 'suv', traverse: 'suv', silverado: 'truck', camaro: 'sports', corvette: 'sports', tahoe: 'fullsize', suburban: 'fullsize', blazer: 'suv', trax: 'economy', bolt: 'electric', colorado: 'truck', _default: 'midsize' },
  bmw:        { '3 series': 'luxury', '330i': 'luxury', '5 series': 'luxury', '7 series': 'luxury', x3: 'luxury_suv', x5: 'luxury_suv', x7: 'luxury_suv', x1: 'luxury_suv', m3: 'sports', m4: 'sports', i4: 'electric', ix: 'electric', _default: 'luxury' },
  mercedes:   { 'c-class': 'luxury', 'c class': 'luxury', 'e-class': 'luxury', 'e class': 'luxury', 's-class': 'luxury', 's class': 'luxury', gle: 'luxury_suv', glc: 'luxury_suv', gls: 'luxury_suv', gla: 'luxury_suv', amg: 'sports', eqe: 'electric', eqs: 'electric', _default: 'luxury' },
  'mercedes-benz': { 'c-class': 'luxury', 'c class': 'luxury', 'e-class': 'luxury', 'e class': 'luxury', 's-class': 'luxury', 's class': 'luxury', gle: 'luxury_suv', glc: 'luxury_suv', gls: 'luxury_suv', gla: 'luxury_suv', amg: 'sports', eqe: 'electric', eqs: 'electric', _default: 'luxury' },
  audi:       { a3: 'luxury', a4: 'luxury', a6: 'luxury', a8: 'luxury', q3: 'luxury_suv', q5: 'luxury_suv', q7: 'luxury_suv', q8: 'luxury_suv', 'e-tron': 'electric', rs: 'sports', _default: 'luxury' },
  lexus:      { is: 'luxury', es: 'luxury', ls: 'luxury', rx: 'luxury_suv', nx: 'luxury_suv', gx: 'luxury_suv', lx: 'luxury_suv', ux: 'luxury_suv', rz: 'electric', _default: 'luxury' },
  hyundai:    { elantra: 'compact', sonata: 'midsize', tucson: 'suv', 'santa fe': 'suv', kona: 'suv', palisade: 'fullsize', ioniq: 'electric', 'ioniq 5': 'electric', 'ioniq 6': 'electric', accent: 'economy', venue: 'economy', _default: 'compact' },
  kia:        { forte: 'compact', k5: 'midsize', optima: 'midsize', sportage: 'suv', telluride: 'suv', sorento: 'suv', soul: 'economy', seltos: 'suv', ev6: 'electric', ev9: 'electric', niro: 'compact', carnival: 'minivan', _default: 'compact' },
  nissan:     { altima: 'midsize', sentra: 'compact', rogue: 'suv', pathfinder: 'suv', murano: 'suv', frontier: 'truck', titan: 'truck', versa: 'economy', kicks: 'economy', leaf: 'electric', ariya: 'electric', maxima: 'fullsize', _default: 'midsize' },
  subaru:     { outback: 'suv', forester: 'suv', crosstrek: 'suv', impreza: 'compact', wrx: 'sports', legacy: 'midsize', ascent: 'suv', solterra: 'electric', _default: 'suv' },
  mazda:      { mazda3: 'compact', mazda6: 'midsize', 'cx-5': 'suv', 'cx-50': 'suv', 'cx-30': 'suv', 'cx-90': 'suv', 'mx-5': 'sports', _default: 'compact' },
  volkswagen: { jetta: 'compact', passat: 'midsize', tiguan: 'suv', atlas: 'suv', taos: 'suv', golf: 'compact', gti: 'sports', id4: 'electric', 'id.4': 'electric', _default: 'compact' },
  tesla:      { 'model 3': 'electric', 'model y': 'electric', 'model s': 'electric', 'model x': 'electric', cybertruck: 'electric', _default: 'electric' },
  jeep:       { wrangler: 'suv', 'grand cherokee': 'suv', cherokee: 'suv', compass: 'suv', gladiator: 'truck', renegade: 'economy', _default: 'suv' },
  ram:        { 1500: 'truck', 2500: 'truck', 3500: 'truck', _default: 'truck' },
  gmc:        { sierra: 'truck', terrain: 'suv', acadia: 'suv', yukon: 'fullsize', canyon: 'truck', hummer: 'electric', _default: 'truck' },
  dodge:      { charger: 'sports', challenger: 'sports', durango: 'suv', hornet: 'suv', _default: 'midsize' },
  volvo:      { s60: 'luxury', s90: 'luxury', xc40: 'luxury_suv', xc60: 'luxury_suv', xc90: 'luxury_suv', c40: 'electric', _default: 'luxury' },
  cadillac:   { ct4: 'luxury', ct5: 'luxury', xt4: 'luxury_suv', xt5: 'luxury_suv', xt6: 'luxury_suv', escalade: 'luxury_suv', lyriq: 'electric', _default: 'luxury' },
  acura:      { integra: 'compact', tlx: 'luxury', mdx: 'luxury_suv', rdx: 'luxury_suv', _default: 'luxury' },
  infiniti:   { q50: 'luxury', q60: 'luxury', qx50: 'luxury_suv', qx60: 'luxury_suv', qx80: 'luxury_suv', _default: 'luxury' },
  lincoln:    { corsair: 'luxury_suv', nautilus: 'luxury_suv', aviator: 'luxury_suv', navigator: 'luxury_suv', _default: 'luxury_suv' },
  genesis:    { g70: 'luxury', g80: 'luxury', g90: 'luxury', gv70: 'luxury_suv', gv80: 'luxury_suv', _default: 'luxury' },
  porsche:    { cayenne: 'luxury_suv', macan: 'luxury_suv', '911': 'sports', taycan: 'electric', panamera: 'luxury', _default: 'luxury' },
  rivian:     { r1t: 'electric', r1s: 'electric', _default: 'electric' },
  lucid:      { air: 'electric', _default: 'electric' },
  buick:      { encore: 'suv', envision: 'suv', enclave: 'suv', _default: 'suv' },
  chrysler:   { pacifica: 'minivan', 300: 'fullsize', _default: 'fullsize' },
  'land rover': { defender: 'luxury_suv', discovery: 'luxury_suv', 'range rover': 'luxury_suv', evoque: 'luxury_suv', _default: 'luxury_suv' },
  jaguar:     { 'f-pace': 'luxury_suv', 'e-pace': 'luxury_suv', 'f-type': 'sports', xe: 'luxury', xf: 'luxury', _default: 'luxury' },
};

// ─── Classification ──────────────────────────────────────────────

function classifyVehicle(make, model) {
  const m = (make || '').toLowerCase().trim();
  const md = (model || '').toLowerCase().trim();
  const brandMap = MAKE_MODEL_MAP[m];
  if (brandMap) {
    // Try exact match first, then partial
    if (brandMap[md]) return brandMap[md];
    for (const [key, cls] of Object.entries(brandMap)) {
      if (key !== '_default' && (md.includes(key) || key.includes(md))) return cls;
    }
    if (brandMap._default) return brandMap._default;
  }
  // Heuristic fallback
  if (/suv|crossover|4x4/i.test(md)) return 'suv';
  if (/truck|pickup/i.test(md)) return 'truck';
  if (/van|minivan/i.test(md)) return 'minivan';
  if (/electric|ev|hybrid/i.test(md)) return 'electric';
  if (/sport|gt|turbo|amg|rs|ss/i.test(md)) return 'sports';
  return 'midsize'; // safe fallback
}

// ─── MSRP Estimation ────────────────────────────────────────────

// Fine-grained MSRP overrides for specific models  (base MSRP in 2024$)
const MSRP_OVERRIDES = {
  'toyota_camry': 28855, 'toyota_corolla': 22995, 'toyota_rav4': 30090,
  'toyota_highlander': 38385, 'toyota_tacoma': 31500, 'toyota_tundra': 39965,
  'honda_civic': 24650, 'honda_accord': 28990, 'honda_cr-v': 30750,
  'honda_pilot': 39150, 'ford_f-150': 36765, 'ford_mustang': 32515,
  'ford_explorer': 36760, 'chevrolet_equinox': 30500, 'chevrolet_silverado': 37645,
  'bmw_3 series': 44450, 'bmw_x3': 48150, 'bmw_x5': 63200,
  'mercedes_c-class': 44950, 'mercedes_gle': 60150, 'audi_a4': 41100,
  'audi_q5': 45600, 'tesla_model 3': 40240, 'tesla_model y': 44990,
  'tesla_model s': 74990, 'hyundai_tucson': 30550, 'hyundai_sonata': 28790,
  'kia_sportage': 30990, 'kia_telluride': 37490, 'nissan_rogue': 30640,
  'jeep_wrangler': 33690, 'jeep_grand cherokee': 40340, 'subaru_outback': 30895,
  'lexus_rx': 49550, 'lexus_es': 42490, 'volvo_xc60': 43350, 'volvo_xc90': 56900,
  'porsche_cayenne': 75650, 'porsche_macan': 60900,
};

function estimateMSRP(make, model, year, vehicleClass) {
  const m = (make || '').toLowerCase().trim();
  const md = (model || '').toLowerCase().trim();
  const currentYear = new Date().getFullYear();
  const yr = parseInt(year) || currentYear;

  // Check overrides first
  const key = `${m}_${md}`;
  let baseMSRP = MSRP_OVERRIDES[key];

  if (!baseMSRP) {
    const cls = VEHICLE_CLASSES[vehicleClass] || VEHICLE_CLASSES.midsize;
    baseMSRP = (cls.msrpRange[0] + cls.msrpRange[1]) / 2;
  }

  // Adjust for year — ~3% inflation/appreciation per year from 2024 baseline
  const yearDiff = yr - 2024;
  baseMSRP = baseMSRP * Math.pow(1.03, yearDiff);

  return Math.round(baseMSRP);
}

// ─── Lease Market Estimation ─────────────────────────────────────

/**
 * Estimate fair-market lease values for a given vehicle.
 *
 * @param {string} make   - Vehicle manufacturer
 * @param {string} model  - Vehicle model
 * @param {string|number} year - Model year
 * @returns {Object} Market data with ranges for lease parameters
 */
export function estimateMarketData(make, model, year) {
  const vehicleClass = classifyVehicle(make, model);
  const cls = VEHICLE_CLASSES[vehicleClass] || VEHICLE_CLASSES.midsize;
  const msrp = estimateMSRP(make, model, year, vehicleClass);

  // ── Monthly payment estimation ──
  // Standard lease formula: ((MSRP - Residual) / Term + (MSRP + Residual) × MoneyFactor)
  const residualValue = Math.round(msrp * cls.residualPct);
  const term = cls.typicalTerm;
  const mf = cls.moneyFactor;
  const depreciation = (msrp - residualValue) / term;
  const financeCharge = (msrp + residualValue) * mf;
  const estimatedMonthly = Math.round(depreciation + financeCharge);

  // APR from money factor:  APR = moneyFactor × 2400
  const estimatedAPR = +(mf * 2400).toFixed(1);

  // Down payment: typically 10-15% of MSRP for a good deal
  const typicalDownPayment = Math.round(msrp * 0.10);

  return {
    vehicleClass,
    estimatedMSRP: msrp,
    monthlyPayment: {
      low:  Math.round(estimatedMonthly * 0.85),
      avg:  estimatedMonthly,
      high: Math.round(estimatedMonthly * 1.20),
      label: 'Monthly Payment',
    },
    interestRate: {
      low:  Math.max(0, +(estimatedAPR - 2).toFixed(1)),
      avg:  estimatedAPR,
      high: +(estimatedAPR + 3).toFixed(1),
      label: 'Interest Rate (APR %)',
    },
    residualValue: {
      low:  Math.round(residualValue * 0.90),
      avg:  residualValue,
      high: Math.round(residualValue * 1.10),
      label: 'Residual Value',
    },
    downPayment: {
      low:  Math.round(typicalDownPayment * 0.50),
      avg:  typicalDownPayment,
      high: Math.round(typicalDownPayment * 2.00),
      label: 'Down Payment',
    },
    annualMileageLimit: {
      low:  10000,
      avg:  12000,
      high: 15000,
      label: 'Annual Mileage Limit',
    },
    leaseTerm: {
      low:  24,
      avg:  36,
      high: 48,
      label: 'Lease Term (months)',
    },
    earlyTerminationFee: {
      low:  200,
      avg:  500,
      high: 1000,
      label: 'Early Termination Fee',
    },
    totalLeaseCost: {
      low:  Math.round((estimatedMonthly * 0.85 * term) + typicalDownPayment * 0.50),
      avg:  Math.round((estimatedMonthly * term) + typicalDownPayment),
      high: Math.round((estimatedMonthly * 1.20 * term) + typicalDownPayment * 2.00),
      label: 'Total Lease Cost',
    },
    source: 'estimated',
    generatedAt: new Date().toISOString(),
  };
}
