# Design Memory - Quick Reference

## 5-Minute Quick Start

### 1. Store a Design
```bash
curl -X POST http://localhost:8000/api/v1/memory/store \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"wn": 1.5, "wp": 2.0, "vdd": 1.8, "temp": 27},
    "outputs": {"freq": 2.5, "power": 100, "delay": 0.4},
    "title": "Design v1",
    "source_scope": "optimization",
    "tags": ["fast", "power-optimized"]
  }'
```

### 2. Search Similar Designs
```bash
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"wn": 1.4, "wp": 2.1, "vdd": 1.8, "temp": 27},
    "top_k": 10,
    "min_similarity": 0.7
  }' | jq
```

### 3. Check Memory Health
```bash
curl http://localhost:8000/api/v1/memory/manage/health \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

### 4. List All Designs
```bash
curl "http://localhost:8000/api/v1/memory/list?limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

## Common Endpoints

### Storage
| Endpoint | Method | Purpose |
|--|--|--|
| `/api/v1/memory/store` | POST | Store a design |
| `/api/v1/memory/search` | POST | Find similar designs |
| `/api/v1/memory/batch-search` | POST | Search multiple queries |
| `/api/v1/memory/list` | GET | List all designs |
| `/api/v1/memory/{id}` | GET | Get specific design |
| `/api/v1/memory/{id}` | DELETE | Delete design |
| `/api/v1/memory/recommend` | POST | Get recommendations |

### Management
| Endpoint | Method | Purpose |
|--|--|--|
| `/api/v1/memory/manage/health` | GET | Memory health report |
| `/api/v1/memory/manage/analysis` | GET | Full analysis |
| `/api/v1/memory/manage/distribution` | GET | Distribution analysis |
| `/api/v1/memory/manage/duplicates` | GET | Find duplicates |
| `/api/v1/memory/manage/cleanup` | POST | Remove old records |
| `/api/v1/memory/manage/consolidate` | POST | Merge duplicates |
| `/api/v1/memory/manage/rebuild-indexes` | POST | Rebuild indexes |

## Python Examples

### Store Design
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/memory/store",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "inputs": {"wn": 1.5, "wp": 2.0, "vdd": 1.8},
        "outputs": {"freq": 2.5, "power": 100},
        "title": "My design",
        "source_scope": "optimization"
    }
)
design_id = response.json()["record_id"]
```

### Search Similar
```python
response = requests.post(
    "http://localhost:8000/api/v1/memory/search",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "inputs": {"wn": 1.5, "wp": 2.0, "vdd": 1.8},
        "top_k": 10
    }
)
hits = response.json()["hits"]
for hit in hits:
    print(f"{hit['title']}: {hit['similarity_score']:.2%}")
```

### Get Recommendations
```python
response = requests.post(
    "http://localhost:8000/api/v1/memory/recommend",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "inputs": {"wn": 1.5, "wp": 2.0},
        "recommendation_type": "similar_designs",
        "count": 5
    }
)
recommendations = response.json()
```

### Monitor Memory
```python
response = requests.get(
    "http://localhost:8000/api/v1/memory/manage/health",
    headers={"Authorization": f"Bearer {token}"}
)
health = response.json()
print(f"Health Score: {health['health_score']}/100")
print(f"Total Designs: {health['total_designs']}")
print(f"Coverage: {health['coverage']:.1f}%")
```

## Feature Vector (18D)

The feature vector encodes design characteristics:

- **Dimensions 1-5:** Transistor dimensions & operating point (wn, wp, vdd, temp, cl_ff)
- **Dimensions 6-7:** Technology & corner (tech, corner)
- **Dimensions 8-10:** Performance (freq, power, delay)
- **Dimensions 11-14:** Quality metrics (fom, health, confidence, reliability)
- **Dimensions 15-18:** Derived features (error%, ratio, sum, scaling)

All vectors are **L2-normalized** for consistent similarity.

## Similarity Scoring

**Similarity Score = cosine_similarity(vector1, vector2)**
- Range: 0.0 (completely different) to 1.0 (identical)
- Typical useful threshold: 0.7 (70% similar)
- High precision: 0.9+ (very similar)

## Memory Limits

| Parameter | Default | Max |
|--|--|--|
| Designs per user | unlimited | 1,000,000 |
| Storage per design | ~2-3 KB | - |
| Storage per user (1000 designs) | ~2-3 MB | - |
| Search results | 5 | 100 |
| Batch queries | 10 | 1000 |

## Health Score Interpretation

| Score | Status | Action |
|--|--|--|
| 90-100 | Excellent | No action needed |
| 80-89 | Good | Regular maintenance |
| 70-79 | Fair | Review & consolidate |
| 50-69 | Poor | Cleanup & rebuild |
| <50 | Critical | Immediate action |

## Maintenance Checklist

```
Weekly:
- [ ] Monitor health score
- [ ] Check for errors in searches

Monthly:
- [ ] Run full analysis
- [ ] Review and consolidate duplicates
- [ ] Check storage usage

Quarterly:
- [ ] Export backup
- [ ] Full memory review
- [ ] Archive old records
```

## Troubleshooting Quick Tips

```bash
# Check server is running
curl http://localhost:8000/health

# Test authentication
curl http://localhost:8000/api/v1/memory/list \
  -H "Authorization: Bearer TOKEN"

# Rebuild indexes (if searches are slow)
curl -X POST http://localhost:8000/api/v1/memory/manage/rebuild-indexes \
  -H "Authorization: Bearer TOKEN"

# Find and consolidate duplicates
curl "http://localhost:8000/api/v1/memory/manage/duplicates?similarity_threshold=0.9" \
  -H "Authorization: Bearer TOKEN"

curl -X POST http://localhost:8000/api/v1/memory/manage/consolidate \
  -H "Authorization: Bearer TOKEN" \
  -d '{"similarity_threshold": 0.95}'
```

## Performance Tips

1. **Fast Searches:** Use `min_similarity=0.8` or higher
2. **Batch Operations:** Use `/batch-search` instead of multiple calls
3. **Large Datasets:** Consolidate duplicates regularly
4. **Index Health:** Rebuild indexes monthly
5. **Memory Usage:** Cleanup records older than 6 months

## Integration Points

### After Optimization
```python
# Store optimization result
await memory_service.store_design(
    inputs=design["inputs"],
    outputs=design["outputs"],
    source_scope="optimization",
    tags=["auto-imported"]
)
```

### During Analysis
```python
# Find similar past designs
similar = await memory_service.search_similar(
    inputs=current_design["inputs"],
    top_k=10
)
```

### For Recommendations
```python
# Get smart recommendations
recommendations = await memory_service.find_recommendations(
    inputs=current_design["inputs"],
    recommendation_type="similar_designs"
)
```

---

**Full Guide:** See `DESIGN_MEMORY_GUIDE.md`  
**Status:** ✅ Ready to Use
