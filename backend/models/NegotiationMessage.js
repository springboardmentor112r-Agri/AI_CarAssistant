import mongoose from 'mongoose';

const negotiationMessageSchema = new mongoose.Schema({
  thread_id:    { type: mongoose.Schema.Types.ObjectId, ref: 'NegotiationThread', required: true },
  sender:       { type: String, enum: ['user', 'assistant'], required: true },
  message_text: { type: String, required: true },
  timestamp:    { type: Date, default: Date.now },
});

export default mongoose.model('NegotiationMessage', negotiationMessageSchema);
