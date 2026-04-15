# ML CMOS Prediction API - Quick Start Guide

**NEW:** Fast XGBoost-based CMOS parameter predictions with confidence scores

---

## 🚀 30-Second Setup

```bash
# 1. Start backend
cd services/api
uvicorn app.main:app --reload

# 2. Train model (in another terminal)
python manage_models.py train --samples 5000

# 3. Make prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"C": 5e-12, "Id": 2e-3, "VDD": 3.3}'
```

Done! ✅

---

## 📋 What You Get

Every prediction returns:

```json
{
  "frequency": {
    "predicted_value": 1.234,
    "confidence": 0.92,
    "upper_bound": 1.456,
    "lower_bound": 1.012,
    "model_r2": 0.92,
    "feature_importance": {"C": 0.45, "Id": 0.35, "VDD": 0.20},
    "timestamp": "2024-01-15T10:30:45.123456"
  },
  "power": { ... },
  "delay": { ... }
}
```

---

## 🎯 All 5 Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/predict` | Single prediction |
| `POST /api/v1/predict/batch` | Multiple predictions |
| `GET /api/v1/predict/models` | Model info |
| `POST /api/v1/predict/train` | Train new model |
| `GET /api/v1/predict/health` | Health check |

---

## 💻 Code Examples

### Python
```python
import requests

resp = requests.post('http://localhost:8000/api/v1/predict',
  json={'C': 5e-12, 'Id': 2e-3, 'VDD': 3.3})

result = resp.json()
print(f"Frequency: {result['frequency']['predicted_value']} GHz")
print(f"Confidence: {result['frequency']['confidence']:.0%}")
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/v1/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ C: 5e-12, Id: 2e-3, VDD: 3.3 })
});
const result = await response.json();
console.log(`Frequency: ${result.frequency.predicted_value} GHz`);
```

---

## 📊 Batch Predictions

```python
# Predict 1000 designs at once
requests.post('http://localhost:8000/api/v1/predict/batch',
  json=[
    {'C': 5e-12, 'Id': 2e-3, 'VDD': 3.3},
    {'C': 1e-12, 'Id': 5e-3, 'VDD': 5.0},
    # ... more designs
  ])
```

---

## 🛠️ Management

```bash
# Train model with custom samples
python manage_models.py train --samples 10000 --name my_model

# List all trained models
python manage_models.py list

# Get model details
python manage_models.py info --name cmos_predictor_v1
```

---

## 🧪 Test Everything

```bash
# Full integration test suite
python test_ml_api.py

# Output shows: ✓ Pass for each test
```

---

## 📈 Expected Performance

- **Accuracy:** R² = 0.90-0.92 (90-92% of variance explained)
- **Confidence:** 88-92% (varies by output)
- **Latency:** 50-100ms per prediction
- **Throughput:** 10-20 predictions/sec (single) or 1000+/sec (batch)

---

## ❓ FAQ

**Q: How do I train a model?**
```bash
python manage_models.py train --samples 10000
```

**Q: How long does training take?**
~2 minutes for 10k samples

**Q: Can I make batch predictions?**
Yes! Up to 1000 per request

**Q: What confidence should I expect?**
0.88-0.92 typical. Higher with more training data

**Q: How do I deploy to production?**
See `ML_PREDICTION_API.md` for deployment guide

---

## 📚 More Info

- **Full API Docs:** Swagger UI at http://localhost:8000/docs
- **Complete Guide:** See `ML_PREDICTION_API.md`
- **Implementation:** See `ML_INTEGRATION_COMPLETE.md`
- **Tests:** See `test_ml_api.py`

---

## 🔗 Integration

### Add to Next.js Dashboard
```typescript
import { useState } from 'react';

export default function PredictorWidget() {
  const [result, setResult] = useState(null);

  async function predict() {
    const resp = await fetch('http://localhost:8000/api/v1/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ C: 5e-12, Id: 2e-3, VDD: 3.3 })
    });
    setResult(await resp.json());
  }

  return (
    <div>
      <button onClick={predict}>Predict</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
```

### Add to Electron Desktop App
```javascript
ipcMain.handle('ml:predict', async (e, params) => {
  const resp = await fetch('http://localhost:8000/api/v1/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  return resp.json();
});
```

---

✅ **Ready to use!** Start backend → Train model → Make predictions
