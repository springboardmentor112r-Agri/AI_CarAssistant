import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import mongoose from 'mongoose';

import authRoutes from './routes/auth.js';
import contractRoutes from './routes/contracts.js';
import slaRoutes from './routes/sla.js';
import vehicleRoutes from './routes/vehicles.js';
import priceRoutes from './routes/prices.js';
import dealerRoutes from './routes/dealers.js';
import negotiationRoutes from './routes/negotiations.js';
import alertRoutes from './routes/alerts.js';
import comparisonRoutes from './routes/comparisons.js';

import Contract from './models/Contract.js';
import ContractSLA from './models/ContractSLA.js';

const app = express();
const PORT = process.env.PORT || 5000;

// ─── Remove existing duplicate contracts ─────────────────────────
async function cleanupDuplicates() {
  try {
    const duplicates = await Contract.aggregate([
      { $group: { _id: { user_id: '$user_id', file_name: '$file_name' }, ids: { $push: '$_id' }, count: { $sum: 1 } } },
      { $match: { count: { $gt: 1 } } },
    ]);
    let removed = 0;
    for (const dup of duplicates) {
      const idsToRemove = dup.ids.slice(1); // keep the first (oldest)
      await ContractSLA.deleteMany({ contract_id: { $in: idsToRemove } });
      await Contract.deleteMany({ _id: { $in: idsToRemove } });
      removed += idsToRemove.length;
    }
    if (removed > 0) console.log(`Cleaned up ${removed} duplicate contract(s)`);
  } catch (err) {
    console.warn('Duplicate cleanup warning:', err.message);
  }
}

// ─── Middleware ──────────────────────────────────────────────────
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// ─── Routes ─────────────────────────────────────────────────────
app.use('/api/auth', authRoutes);
app.use('/api/contracts', contractRoutes);
app.use('/api/sla', slaRoutes);
app.use('/api/vehicles', vehicleRoutes);
app.use('/api/prices', priceRoutes);
app.use('/api/dealers', dealerRoutes);
app.use('/api/negotiations', negotiationRoutes);
app.use('/api/alerts', alertRoutes);
app.use('/api/comparisons', comparisonRoutes);

app.get('/api/health', (_req, res) => res.json({ status: 'ok' }));

// ─── Connect to MongoDB & Start ─────────────────────────────────
mongoose
  .connect(process.env.MONGODB_URI)
  .then(async () => {
    console.log('Connected to MongoDB Atlas');
    await cleanupDuplicates();
    app.listen(PORT, () => console.log(`Backend running on http://localhost:${PORT}`));
  })
  .catch((err) => {
    console.error('MongoDB connection error:', err.message);
    process.exit(1);
  });
