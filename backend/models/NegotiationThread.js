import mongoose from 'mongoose';

const negotiationThreadSchema = new mongoose.Schema({
  user_id:     { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  contract_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Contract', default: null },
  dealer_id:   { type: mongoose.Schema.Types.ObjectId, ref: 'Dealer', default: null },
  created_at:  { type: Date, default: Date.now },
});

export default mongoose.model('NegotiationThread', negotiationThreadSchema);
