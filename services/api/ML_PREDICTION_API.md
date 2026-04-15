# ML Prediction API Documentation

## Overview

The ML Prediction API provides machine learning-based predictions for CMOS circuit parameters using trained XGBoost models. It accepts capacitance (C), drain current (Id), and supply voltage (VDD) as inputs and predicts:

- **Frequency** (GHz)
- **Power** (mW)
- **Delay** (ns)

Each prediction includes confidence scores and 95% confidence intervals.

## API Endpoints

### 1. Make Prediction

**Endpoint:** `POST /api/v1/predict`

**Description:** Make a single prediction with confidence scores.

**Request:**
```json
{
  "C": 5e-12,
  "Id": 2e-3,
  "VDD": 3.3
}
```

**Parameters:**
- `C` (float, required): Capacitance in farads (must be > 0)
- `Id` (float, required): Drain current in amperes (must be > 0)
- `VDD` (float, required): Supply voltage in volts (must be > 0)

**Response:**
```json
{
  "frequency": {
    "predicted_value": 1.234,
    "confidence": 0.92,
    "upper_bound": 1.456,
    "lower_bound": 1.012,
    "model_r2": 0.92,
    "feature_importance": {
      "C": 0.45,
      "Id": 0.35,
      "VDD": 0.20
    },
    "timestamp": "2024-01-15T10:30:45.123456"
  },
  "power": { ... },
  "delay": { ... }
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "C": 5e-12,
    "Id": 2e-3,
    "VDD": 3.3
  }'
```

**Example Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/predict",
    json={
        "C": 5e-12,
        "Id": 2e-3,
        "VDD": 3.3
    }
)

print(response.json())
```

---

### 2. Batch Prediction

**Endpoint:** `POST /api/v1/predict/batch`

**Description:** Make predictions for multiple inputs at once.

**Request:**
```json
[
  {"C": 5e-12, "Id": 2e-3, "VDD": 3.3},
  {"C": 1e-12, "Id": 5e-3, "VDD": 5.0},
  {"C": 10e-12, "Id": 1e-3, "VDD": 1.8}
]
```

**Response:**
```json
[
  { /* prediction object 1 */ },
  { /* prediction object 2 */ },
  { /* prediction object 3 */ }
]
```

**Example Python:**
```python
import requests

requests_list = [
    {"C": 5e-12, "Id": 2e-3, "VDD": 3.3},
    {"C": 1e-12, "Id": 5e-3, "VDD": 5.0},
]

response = requests.post(
    "http://localhost:8000/api/v1/predict/batch",
    json=requests_list
)

predictions = response.json()
```

---

### 3. Get Model Information

**Endpoint:** `GET /api/v1/predict/models`

**Description:** Get information about the currently loaded model.

**Response:**
```json
{
  "trained": true,
  "training_date": "2024-01-15T10:00:00",
  "training_samples": 10000,
  "feature_names": ["C", "Id", "VDD"],
  "performance_metrics": {
    "frequency": {
      "r2": 0.92,
      "rmse": 0.123,
      "mae": 0.089,
      "cv_r2_mean": 0.91,
      "cv_r2_std": 0.02
    },
    ...
  }
}
```

---

### 4. Train New Model

**Endpoint:** `POST /api/v1/predict/train`

**Description:** Train a new XGBoost model on synthetic CMOS data.

⚠️ **Note:** This is a long-running operation (several minutes). Use with caution in production.

**Request:**
```json
{
  "n_samples": 10000,
  "model_name": "cmos_predictor_v2"
}
```

**Parameters:**
- `n_samples` (integer, optional): Number of training samples (1000-100000, default: 10000)
- `model_name` (string, optional): Name to save model as (default: "cmos_predictor_v1")

**Response:**
```json
{
  "status": "success",
  "message": "Model trained and saved as cmos_predictor_v2",
  "model_name": "cmos_predictor_v2",
  "training_samples": 10000,
  "performance_metrics": {
    "frequency": {
      "r2": 0.92,
      "rmse": 0.123,
      ...
    },
    ...
  }
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/predict/train \
  -H "Content-Type: application/json" \
  -d '{"n_samples": 5000}'
```

---

### 5. Health Check

**Endpoint:** `GET /api/v1/predict/health`

**Description:** Check if the prediction service is ready.

**Response:**
```json
{
  "status": "healthy",
  "model_trained": true,
  "training_date": "2024-01-15T10:00:00",
  "training_samples": 10000
}
```

---

## Models and Parameters

### Output Variables

| Variable | Unit | Range | Description |
|----------|------|-------|-------------|
| Frequency | GHz | 0.1 - 10 | Operating frequency |
| Power | mW | 0.01 - 1000 | Power consumption |
| Delay | ns | 0.01 - 100 | Propagation delay |

### Input Parameters

| Parameter | Unit | Typical Range |
|-----------|------|---------------|
| C | Farads | 1e-12 - 10e-12 (1-10 pF) |
| Id | Amperes | 0.5e-3 - 10e-3 (0.5-10 mA) |
| VDD | Volts | 1.2 - 5.0 |

### Confidence Scoring

Confidence is calculated as:
$$\text{Confidence} = R^2 \text{ score (0 to 1)}$$

Where:
- **1.0** = Perfect prediction (R² = 1.0)
- **0.9** = Very good (R² = 0.9)
- **0.7** = Good (R² = 0.7)
- **0.5** = Fair (R² = 0.5)
- **< 0.5** = Poor

### Confidence Intervals

95% confidence intervals are calculated as:
$$CI = \text{Prediction} \pm 1.96 \times \text{RMSE}$$

---

## Management Script

Use the management script to train and manage models from the command line:

**Installation:**
```bash
cd services/api
```

**Train Model:**
```bash
python manage_models.py train --samples 10000 --name cmos_predictor_v1
```

**List Models:**
```bash
python manage_models.py list
```

**Get Model Info:**
```bash
python manage_models.py info --name cmos_predictor_v1
```

---

## Error Handling

### 400 Bad Request
- Invalid input parameters (e.g., negative values)
- Missing required fields

### 503 Service Unavailable
- Model not trained yet
- Call `/api/v1/predict/train` endpoint first

### 500 Internal Server Error
- Unexpected server error
- Check logs for details

---

## Usage Examples

### Python Integration

```python
import requests
import json

# Initialize API client
API_URL = "http://localhost:8000/api/v1/predict"

def predict_cmos(C, Id, VDD):
    """Make a CMOS prediction."""
    response = requests.post(
        f"{API_URL}",
        json={"C": C, "Id": Id, "VDD": VDD}
    )
    return response.json()

def check_model_status():
    """Check if model is trained."""
    response = requests.get(f"{API_URL}/health")
    return response.json()

# Example usage
if __name__ == "__main__":
    # Check model status
    status = check_model_status()
    print(f"Model Status: {status}")
    
    # Make prediction
    predictions = predict_cmos(
        C=5e-12,      # 5 pF
        Id=2e-3,      # 2 mA
        VDD=3.3       # 3.3 V
    )
    
    print(f"\nFrequency Prediction:")
    print(f"  Value: {predictions['frequency']['predicted_value']:.3f} GHz")
    print(f"  Confidence: {predictions['frequency']['confidence']:.1%}")
    print(f"  95% CI: [{predictions['frequency']['lower_bound']:.3f}, "
          f"{predictions['frequency']['upper_bound']:.3f}]")
```

### JavaScript/Node.js Integration

```javascript
// Make a prediction
async function predict(C, Id, VDD) {
  const response = await fetch('http://localhost:8000/api/v1/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ C, Id, VDD })
  });
  return response.json();
}

// Usage
const prediction = await predict(5e-12, 2e-3, 3.3);
console.log(`Frequency: ${prediction.frequency.predicted_value} GHz`);
console.log(`Confidence: ${(prediction.frequency.confidence * 100).toFixed(1)}%`);
```

---

## Performance Metrics

The model is trained using 5-fold cross-validation. Typical performance:

| Metric | Frequency | Power | Delay |
|--------|-----------|-------|-------|
| R² | 0.92 | 0.88 | 0.90 |
| RMSE | 0.15 GHz | 12.5 mW | 2.3 ns |
| MAE | 0.10 GHz | 8.2 mW | 1.5 ns |

*Note: Actual performance depends on training data and hyperparameters.*

---

## Troubleshooting

**Issue: "Model not trained" error**

Solution: Call the `/train` endpoint first:
```bash
curl -X POST http://localhost:8000/api/v1/predict/train
```

**Issue: Service unavailable**

Solution: Check that all dependencies are installed:
```bash
pip install -r requirements.txt
```

**Issue: Slow predictions**

Solution: This is normal for the first prediction. Models are loaded on-demand and cached afterwards.

---

## Architecture

```
FastAPI Server
    ├── /api/v1/predict (POST) → Single prediction
    ├── /api/v1/predict/batch (POST) → Batch predictions
    ├── /api/v1/predict/models (GET) → Model info
    ├── /api/v1/predict/train (POST) → Train new model
    └── /api/v1/predict/health (GET) → Health check

↓ (Uses)

XGBoostCMOSPredictor
    ├── Models (xgboost)
    │   ├── frequency_model
    │   ├── power_model
    │   └── delay_model
    ├── Feature Scaler (StandardScaler)
    └── Target Scalers (one per output)

↓ (Loads from)

Trained Models Directory (./models/)
    ├── cmos_predictor_v1/
    │   ├── frequency_model.json
    │   ├── power_model.json
    │   ├── delay_model.json
    │   ├── scaler_features.pkl
    │   ├── scaler_target_*.pkl
    │   └── metadata.json
    └── cmos_predictor_v2/
        └── ...
```

---

## References

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [scikit-learn Scaling](https://scikit-learn.org/stable/modules/preprocessing.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
