import { Router } from 'express';
import Contract from '../models/Contract.js';
import ContractSLA from '../models/ContractSLA.js';
import auth from '../middleware/auth.js';

const router = Router();

// Create (with duplicate check)
router.post('/', auth, async (req, res) => {
  try {
    const existing = await Contract.findOne({
      user_id: req.userId,
      file_name: req.body.file_name,
    });
    if (existing) {
      return res.status(409).json({ error: 'duplicate', message: 'This contract has already been uploaded.', contractId: existing._id });
    }
    const contract = await Contract.create({ ...req.body, user_id: req.userId });
    res.status(201).json(contract);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Check if contract exists by file name
router.get('/check', auth, async (req, res) => {
  try {
    const fileName = req.query.file_name;
    if (!fileName) return res.status(400).json({ error: 'file_name query param required' });
    const existing = await Contract.findOne({ user_id: req.userId, file_name: fileName });
    res.json({ exists: !!existing, contractId: existing?._id || null });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Remove duplicate contracts (keeps the oldest, removes newer duplicates and their SLAs)
router.post('/cleanup-duplicates', auth, async (req, res) => {
  try {
    const contracts = await Contract.find({ user_id: req.userId }).sort({ upload_date: 1 });
    const seen = new Map();
    let removed = 0;
    for (const c of contracts) {
      if (seen.has(c.file_name)) {
        await ContractSLA.deleteMany({ contract_id: c._id });
        await Contract.findByIdAndDelete(c._id);
        removed++;
      } else {
        seen.set(c.file_name, c._id);
      }
    }
    res.json({ message: `Removed ${removed} duplicate(s)`, removed });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// List for current user
router.get('/', auth, async (req, res) => {
  try {
    const contracts = await Contract.find({ user_id: req.userId }).sort({ upload_date: -1 });
    res.json(contracts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get one
router.get('/:id', auth, async (req, res) => {
  try {
    const contract = await Contract.findOne({ _id: req.params.id, user_id: req.userId });
    if (!contract) return res.status(404).json({ error: 'Not found' });
    res.json(contract);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update
router.put('/:id', auth, async (req, res) => {
  try {
    const contract = await Contract.findOneAndUpdate(
      { _id: req.params.id, user_id: req.userId },
      req.body,
      { new: true }
    );
    if (!contract) return res.status(404).json({ error: 'Not found' });
    res.json(contract);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Delete
router.delete('/:id', auth, async (req, res) => {
  try {
    const contract = await Contract.findOneAndDelete({ _id: req.params.id, user_id: req.userId });
    if (!contract) return res.status(404).json({ error: 'Not found' });
    res.json({ message: 'Deleted' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
