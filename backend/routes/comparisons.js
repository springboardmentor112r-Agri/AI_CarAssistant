import { Router } from 'express';
import OfferComparison from '../models/OfferComparison.js';
import auth from '../middleware/auth.js';

const router = Router();

// Create
router.post('/', auth, async (req, res) => {
  try {
    const comparison = await OfferComparison.create({ ...req.body, user_id: req.userId });
    res.status(201).json(comparison);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get all for current user
router.get('/', auth, async (req, res) => {
  try {
    const comparisons = await OfferComparison.find({ user_id: req.userId }).sort({ created_at: -1 });
    res.json(comparisons);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Delete
router.delete('/:id', auth, async (req, res) => {
  try {
    await OfferComparison.findOneAndDelete({ _id: req.params.id, user_id: req.userId });
    res.json({ message: 'Deleted' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
