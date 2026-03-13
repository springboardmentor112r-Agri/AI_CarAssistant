import mongoose from 'mongoose';

const alertSchema = new mongoose.Schema({
  contract_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Contract', required: true },
  alert_type:  { type: String, required: true },
  description: { type: String, default: '' },
  severity:    { type: String, enum: ['low', 'medium', 'high', 'critical'], default: 'medium' },
  created_at:  { type: Date, default: Date.now },
});

export default mongoose.model('Alert', alertSchema);
