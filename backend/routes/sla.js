import { Router } from 'express';
import ContractSLA from '../models/ContractSLA.js';
import Contract from '../models/Contract.js';
import auth from '../middleware/auth.js';

const router = Router();

// Save extracted SLA for a contract
router.post('/', auth, async (req, res) => {
  try {
    const { contract_id, ...slaFields } = req.body;
    // Verify the user owns the contract
    const contract = await Contract.findOne({ _id: contract_id, user_id: req.userId });
    if (!contract) return res.status(404).json({ error: 'Contract not found' });

    const sla = await ContractSLA.create({ contract_id, ...slaFields });
    res.status(201).json(sla);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get SLA by contract
router.get('/contract/:contractId', auth, async (req, res) => {
  try {
    const contract = await Contract.findOne({ _id: req.params.contractId, user_id: req.userId });
    if (!contract) return res.status(404).json({ error: 'Contract not found' });

    const sla = await ContractSLA.findOne({ contract_id: req.params.contractId });
    if (!sla) return res.status(404).json({ error: 'SLA not found' });
    res.json(sla);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get all SLAs for current user
router.get('/', auth, async (req, res) => {
  try {
    const contracts = await Contract.find({ user_id: req.userId }).select('_id');
    const ids = contracts.map((c) => c._id);
    const slas = await ContractSLA.find({ contract_id: { $in: ids } });
    res.json(slas);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get all SLAs with contract details (for compare tab)
router.get('/with-contracts', auth, async (req, res) => {
  try {
    const contracts = await Contract.find({ user_id: req.userId }).sort({ upload_date: -1 });
    const contractIds = contracts.map((c) => c._id);
    const slas = await ContractSLA.find({ contract_id: { $in: contractIds } });

    const contractMap = {};
    for (const c of contracts) {
      contractMap[c._id.toString()] = c;
    }

    const results = slas.map((sla) => {
      const contract = contractMap[sla.contract_id.toString()];
      return {
        id: sla._id.toString(),
        contractId: sla.contract_id.toString(),
        fileName: contract?.file_name || 'Unknown',
        timestamp: contract?.upload_date || sla._id.getTimestamp(),
        slaData: sla.raw_sla_json || {},
        extractionMethod: 'text',
      };
    });

    res.json(results);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Delete
router.delete('/:id', auth, async (req, res) => {
  try {
    await ContractSLA.findByIdAndDelete(req.params.id);
    res.json({ message: 'Deleted' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
