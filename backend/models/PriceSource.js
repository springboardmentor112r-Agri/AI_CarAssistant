import mongoose from 'mongoose';

const rangeSchema = new mongoose.Schema({
  low:   { type: Number },
  avg:   { type: Number },
  high:  { type: Number },
  label: { type: String },
}, { _id: false });

const priceSourceSchema = new mongoose.Schema({
  // Legacy fields
  vehicle_id:    { type: mongoose.Schema.Types.ObjectId, ref: 'Vehicle' },
  source:        { type: String, default: 'estimated' },
  price_min:     { type: Number, default: null },
  price_max:     { type: Number, default: null },
  avg_price:     { type: Number, default: null },
  market_region: { type: String, default: '' },

  // Market data fields
  make:               { type: String, required: true },
  model:              { type: String, required: true },
  year:               { type: String, required: true },
  vehicleClass:       { type: String },
  estimatedMSRP:      { type: Number },
  monthlyPayment:     rangeSchema,
  interestRate:       rangeSchema,
  residualValue:      rangeSchema,
  downPayment:        rangeSchema,
  annualMileageLimit: rangeSchema,
  leaseTerm:          rangeSchema,
  earlyTerminationFee: rangeSchema,
  totalLeaseCost:     rangeSchema,
  generatedAt:        { type: Date, default: Date.now },
}, { timestamps: true });

priceSourceSchema.index({ make: 1, model: 1, year: 1 });

export default mongoose.model('PriceSource', priceSourceSchema);
