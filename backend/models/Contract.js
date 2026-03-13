import mongoose from 'mongoose';

const contractSchema = new mongoose.Schema({
  user_id:        { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  file_name:      { type: String, required: true },
  file_path:      { type: String, default: '' },
  upload_date:    { type: Date, default: Date.now },
  extracted_text: { type: String, default: '' },
  status:         { type: String, enum: ['uploaded', 'processing', 'extracted', 'failed'], default: 'uploaded' },
});

contractSchema.index({ user_id: 1, file_name: 1 }, { unique: true });

export default mongoose.model('Contract', contractSchema);
