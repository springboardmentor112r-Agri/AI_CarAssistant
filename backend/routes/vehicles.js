import { Router } from 'express';
import Vehicle from '../models/Vehicle.js';
import auth from '../middleware/auth.js';

const router = Router();

// Create / upsert by VIN
router.post('/', auth, async (req, res) => {
  try {
    const vehicle = await Vehicle.findOneAndUpdate(
      { vin_number: req.body.vin_number },
      req.body,
      { new: true, upsert: true }
    );
    res.status(201).json(vehicle);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get by VIN
router.get('/vin/:vin', auth, async (req, res) => {
  try {
    const vehicle = await Vehicle.findOne({ vin_number: req.params.vin });
    if (!vehicle) return res.status(404).json({ error: 'Vehicle not found' });
    res.json(vehicle);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get by ID
router.get('/:id', auth, async (req, res) => {
  try {
    const vehicle = await Vehicle.findById(req.params.id);
    if (!vehicle) return res.status(404).json({ error: 'Vehicle not found' });
    res.json(vehicle);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
