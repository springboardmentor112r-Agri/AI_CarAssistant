import mongoose from 'mongoose';

const dealerSchema = new mongoose.Schema({
  dealer_name:   { type: String, required: true },
  location:      { type: String, default: '' },
  contact_email: { type: String, default: '' },
  phone:         { type: String, default: '' },
});

export default mongoose.model('Dealer', dealerSchema);
