import { Router } from 'express';
import PriceSource from '../models/PriceSource.js';
import { estimateMarketData } from '../services/marketData.js';
import auth from '../middleware/auth.js';

const router = Router();

// Create
router.post('/', auth, async (req, res) => {
  try {
    const price = await PriceSource.create(req.body);
    res.status(201).json(price);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get by vehicle
router.get('/vehicle/:vehicleId', auth, async (req, res) => {
  try {
    const prices = await PriceSource.find({ vehicle_id: req.params.vehicleId });
    res.json(prices);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get market data for a vehicle by make/model/year
router.get('/market/:make/:model/:year', auth, async (req, res) => {
  try {
    const { make, model, year } = req.params;
    const makeLower = make.toLowerCase().trim();
    const modelLower = model.toLowerCase().trim();
    const yearStr = String(year).trim();

    // Check cache (valid for 7 days)
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    let cached = await PriceSource.findOne({
      make: makeLower,
      model: modelLower,
      year: yearStr,
      generatedAt: { $gte: sevenDaysAgo },
    });

    if (cached) {
      return res.json(cached);
    }

    // Generate fresh market data
    const marketData = estimateMarketData(makeLower, modelLower, yearStr);

    // Upsert into cache
    cached = await PriceSource.findOneAndUpdate(
      { make: makeLower, model: modelLower, year: yearStr },
      { ...marketData, make: makeLower, model: modelLower, year: yearStr },
      { upsert: true, new: true, setDefaultsOnInsert: true }
    );

    res.json(cached);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
