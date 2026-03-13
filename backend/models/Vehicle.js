import mongoose from 'mongoose';

const vehicleSchema = new mongoose.Schema({
  vin_number:     { type: String, required: true, unique: true },
  make:           { type: String, default: '' },
  model:          { type: String, default: '' },
  year:           { type: String, default: '' },
  engine:         { type: String, default: '' },
  fuel_type:      { type: String, default: '' },
  transmission:   { type: String, default: '' },
  recall_history: { type: [mongoose.Schema.Types.Mixed], default: [] },
});

export default mongoose.model('Vehicle', vehicleSchema);
