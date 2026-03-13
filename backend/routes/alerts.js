import { Router } from 'express';
import Alert from '../models/Alert.js';
import Contract from '../models/Contract.js';
import auth from '../middleware/auth.js';

const router = Router();

// Create alert
router.post('/', auth, async (req, res) => {
  try {
    const alert = await Alert.create(req.body);
    res.status(201).json(alert);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get alerts for a contract
router.get('/contract/:contractId', auth, async (req, res) => {
  try {
    const alerts = await Alert.find({ contract_id: req.params.contractId }).sort({ created_at: -1 });
    res.json(alerts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get all alerts for current user's contracts
router.get('/', auth, async (req, res) => {
  try {
    const contracts = await Contract.find({ user_id: req.userId }).select('_id');
    const ids = contracts.map((c) => c._id);
    const alerts = await Alert.find({ contract_id: { $in: ids } }).sort({ created_at: -1 });
    res.json(alerts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Delete
router.delete('/:id', auth, async (req, res) => {
  try {
    await Alert.findByIdAndDelete(req.params.id);
    res.json({ message: 'Deleted' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
