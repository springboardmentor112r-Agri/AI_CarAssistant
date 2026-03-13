import { Router } from 'express';
import NegotiationThread from '../models/NegotiationThread.js';
import NegotiationMessage from '../models/NegotiationMessage.js';
import Contract from '../models/Contract.js';
import auth from '../middleware/auth.js';

const router = Router();

// Create thread
router.post('/threads', auth, async (req, res) => {
  try {
    const { contract_id, dealer_id } = req.body;
    // If contract_id is provided, verify ownership
    if (contract_id) {
      const contract = await Contract.findOne({ _id: contract_id, user_id: req.userId });
      if (!contract) return res.status(404).json({ error: 'Contract not found' });
    }

    const thread = await NegotiationThread.create({
      user_id: req.userId,
      contract_id: contract_id || null,
      dealer_id: dealer_id || null,
    });
    res.status(201).json(thread);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// List threads for a contract
router.get('/threads/contract/:contractId', auth, async (req, res) => {
  try {
    const threads = await NegotiationThread.find({ contract_id: req.params.contractId }).sort({ created_at: -1 });
    res.json(threads);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// List all threads for current user
router.get('/threads', auth, async (req, res) => {
  try {
    const threads = await NegotiationThread.find({ user_id: req.userId }).sort({ created_at: -1 });
    res.json(threads);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Add message to thread
router.post('/messages', auth, async (req, res) => {
  try {
    const msg = await NegotiationMessage.create(req.body);
    res.status(201).json(msg);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get messages in a thread
router.get('/messages/:threadId', auth, async (req, res) => {
  try {
    const msgs = await NegotiationMessage.find({ thread_id: req.params.threadId }).sort({ timestamp: 1 });
    res.json(msgs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
