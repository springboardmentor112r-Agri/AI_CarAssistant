import mongoose from 'mongoose';

const offerComparisonSchema = new mongoose.Schema({
  user_id:           { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  contract_id:       { type: mongoose.Schema.Types.ObjectId, ref: 'Contract', required: true },
  fair_price:        { type: Number, default: null },
  comparison_result: { type: mongoose.Schema.Types.Mixed, default: {} },
  created_at:        { type: Date, default: Date.now },
});

export default mongoose.model('OfferComparison', offerComparisonSchema);
