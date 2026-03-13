import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  name:          { type: String, required: true, trim: true },
  email:         { type: String, required: true, unique: true, lowercase: true, trim: true },
  password_hash: { type: String, required: true },
  created_at:    { type: Date, default: Date.now },
  last_login:    { type: Date, default: null },
});

export default mongoose.model('User', userSchema);
