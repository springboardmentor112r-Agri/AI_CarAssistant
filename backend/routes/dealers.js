import { Router } from 'express';
import Dealer from '../models/Dealer.js';
import auth from '../middleware/auth.js';

const router = Router();

// Create
router.post('/', auth, async (req, res) => {
  try {
    const dealer = await Dealer.create(req.body);
    res.status(201).json(dealer);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// List all
router.get('/', auth, async (req, res) => {
  try {
    const dealers = await Dealer.find();
    res.json(dealers);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get one
router.get('/:id', auth, async (req, res) => {
  try {
    const dealer = await Dealer.findById(req.params.id);
    if (!dealer) return res.status(404).json({ error: 'Not found' });
    res.json(dealer);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
