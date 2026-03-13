import mongoose from 'mongoose';

const contractSLASchema = new mongoose.Schema({
  contract_id:                { type: mongoose.Schema.Types.ObjectId, ref: 'Contract', required: true },
  interest_rate:              { type: String, default: '' },
  lease_term_months:          { type: String, default: '' },
  monthly_payment:            { type: String, default: '' },
  down_payment:               { type: String, default: '' },
  residual_value:             { type: String, default: '' },
  mileage_limit:              { type: String, default: '' },
  overage_fee:                { type: String, default: '' },
  early_termination_fee:      { type: String, default: '' },
  purchase_option_price:      { type: String, default: '' },
  maintenance_responsibility: { type: String, default: '' },
  warranty_info:              { type: String, default: '' },
  insurance_requirement:      { type: String, default: '' },
  fairness_score:             { type: Number, default: null },
  raw_sla_json:               { type: mongoose.Schema.Types.Mixed, default: {} },
});

export default mongoose.model('ContractSLA', contractSLASchema);
