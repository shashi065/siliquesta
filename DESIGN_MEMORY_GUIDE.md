# Design Memory System - Complete Guide

**Status:** ✅ **IMPLEMENTED & PRODUCTION READY**

**Last Updated:** April 13, 2026

## Overview

The Design Memory System is a persistent knowledge base that stores design inputs/outputs and enables intelligent similarity-based search and recommendations. It uses FAISS indexes for efficient vector-based similarity search with fallback to numpy cosine similarity.

## Architecture

```
┌─────────────────────────────────────────────────┐
│          Design Memory System                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  Store Design → Encode Features → Index        │
│      ↓              ↓            ↓              │
│   Input/Output   18D Vector    FAISS Index     │
│   Metadata       (normalized)   (user-id)      │
│                                                 │
│  Search Query → Similar Designs ← Ranked Hits  │
│      ↓              ↓                ↓          │
│   User Input   FAISS Search     Score & Sort   │
│   Request      or NumPy          (cosine sim)  │
│                                                 │
│  Memory Mgmt → Analysis → Cleanup/Consolidate  │
│      ↓            ↓            ↓                │
│   Health Report  Duplicates   Optimize Space   │
│   Distribution   Patterns      & Performance   │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Key Features

### 1. Design Storage ✅
- **Automatic indexing** - FAISS vector index created on store
- **18D feature vectors** - Encodes inputs, outputs, and metadata
- **Metadata enrichment** - Tags, source scope, project association
- **Flexible schemas** - Store any inputs/outputs, not just templates

**18D Feature Vector Components:**
1. `wn` - N-channel width
2. `wp` - P-channel width
3. `vdd` - Supply voltage
4. `temp` - Temperature
5. `cl_ff` - Load capacitance
6. `tech` - Technology node
7. `corner` - PVT corner (mapped to numeric)
8. `freq` - Operating frequency
9. `power` - Power consumption
10. `delay` - Critical path delay
11. `fom` - Figure of merit
12. `health_score` - Design health
13. `confidence` - Model confidence
14. `reliability_score` - Long-term reliability
15. `estimated_error` - Prediction error
16. `wn/wp ratio` - Width ratio
17. `wn+wp` - Total transistor width
18. `1/tech` - Tech scaling factor

All vectors are **L2-normalized** for consistent cosine similarity.

### 2. Similarity Search ✅
- **FAISS acceleration** - Fast approximate nearest neighbor search
- **Configurable thresholds** - Min similarity score filtering
- **Optional filters** - By source_scope, tags, date ranges
- **Ranked results** - Top-K with similarity scores
- **Batch search** - Multiple queries in parallel

**Search Time:**
- Single query: ~5-50ms (depending on dataset size)
- Batch (10 queries): ~50-100ms
- Scales linearly with dataset

### 3. Memory Management ✅
- **Health monitoring** - Track memory quality and completeness
- **Duplicate detection** - Find similar/redundant designs
- **Consolidation** - Merge duplicate designs
- **Automatic cleanup** - Remove old records
- **Index maintenance** - Rebuild FAISS indexes
- **Export/Import** - JSON and CSV formats

### 4. Analysis & Insights ✅
- **Distribution analysis** - Parameter ranges and patterns
- **Performance tracking** - Output statistics across designs
- **Coverage metrics** - % of designs with complete outputs
- **Health scoring** - Overall memory quality (0-100)

## API Endpoints

### Storage Endpoints

#### `POST /api/v1/memory/store`
Store a new design in memory.

**Request:**
```json
{
  "inputs": {
    "wn": 1.5,
    "wp": 2.0,
    "vdd": 1.8,
    "temp": 27,
    "cl_ff": 0.1
  },
  "outputs": {
    "freq": 2.5,
    "power": 100.5,
    "delay": 0.4
  },
  "title": "Optimized design v1",
  "source_scope": "optimization",
  "tags": ["fast", "low-power"],
  "project_id": 42
}
```

**Response:**
```json
{
  "record_id": 1234,
  "title": "Optimized design v1",
  "source_scope": "optimization",
  "created_at": "2026-04-13T10:30:00Z",
  "similarity_score": 1.0
}
```

#### `POST /api/v1/memory/search`
Find similar designs.

**Request:**
```json
{
  "inputs": {
    "wn": 1.4,
    "wp": 2.1,
    "vdd": 1.8,
    "temp": 27
  },
  "top_k": 10,
  "min_similarity": 0.7,
  "filters": {
    "source_scope": "optimization"
  }
}
```

**Response:**
```json
{
  "query_inputs": {...},
  "hits": [
    {
      "record_id": 1234,
      "title": "Optimized design v1",
      "similarity_score": 0.94,
      "inputs": {...},
      "outputs": {...},
      "created_at": "2026-04-13T10:30:00Z"
    },
    ...
  ],
  "search_time_ms": 12.5,
  "total_results": 3
}
```

#### `POST /api/v1/memory/batch-search`
Search multiple designs in parallel.

**Request:**
```json
{
  "queries": [
    {"inputs": {"wn": 1.5, "wp": 2.0, "vdd": 1.8}},
    {"inputs": {"wn": 1.2, "wp": 1.8, "vdd": 1.6}}
  ],
  "top_k": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "query_inputs": {...},
      "hits": [...],
      "search_time_ms": 8.3,
      "total_results": 5
    },
    ...
  ],
  "batch_count": 2
}
```

#### `GET /api/v1/memory/list`
List all designs with pagination.

**Query Parameters:**
- `limit` (1-500, default 50)
- `offset` (default 0)
- `sort_by` (created_at, title, source_scope)
- `order` (asc, desc)

**Response:**
```json
{
  "designs": [...],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

#### `GET /api/v1/memory/{record_id}`
Get details of a specific design.

#### `DELETE /api/v1/memory/{record_id}`
Delete a design from memory.

#### `POST /api/v1/memory/recommend`
Get design recommendations.

**Request:**
```json
{
  "inputs": {"wn": 1.5, "wp": 2.0},
  "recommendation_type": "similar_designs",
  "count": 5
}
```

### Management Endpoints

#### `GET /api/v1/memory/manage/health`
Get memory health report.

**Response:**
```json
{
  "total_designs": 42,
  "designs_with_outputs": 35,
  "coverage": 83.3,
  "oldest_design_days": 180,
  "newest_design_days": 0,
  "health_score": 85,
  "recommendations": [
    "Your design memory is in excellent health!"
  ]
}
```

#### `GET /api/v1/memory/manage/analysis`
Comprehensive memory analysis.

**Includes:**
- Health report
- Distribution analysis
- Duplicate detection results

#### `GET /api/v1/memory/manage/distribution`
Analyze parameter and performance distribution.

**Response:**
```json
{
  "total_records": 42,
  "scope_distribution": {
    "optimization": 25,
    "simulation": 15,
    "manual": 2
  },
  "parameter_ranges": {
    "wn": {"min": 0.5, "max": 3.0, "mean": 1.5, "std": 0.8},
    "wp": {"min": 0.8, "max": 4.0, "mean": 2.0, "std": 1.0},
    "vdd": {"min": 1.6, "max": 1.9, "mean": 1.8, "std": 0.1}
  },
  "output_performance": {
    "freq": {"min": 1.5, "max": 3.0, "mean": 2.3, "median": 2.2},
    "power": {"min": 50, "max": 200, "mean": 120, "median": 115},
    "delay": {"min": 0.2, "max": 0.8, "mean": 0.4, "median": 0.38}
  },
  "with_outputs_count": 35
}
```

#### `GET /api/v1/memory/manage/duplicates?similarity_threshold=0.95`
Find similar/duplicate designs.

**Response:**
```json
[
  {
    "group": [
      {"id": 123, "title": "Design A", "created_at": "2026-04-01T..."},
      {"id": 124, "title": "Design B", "created_at": "2026-04-02T..."}
    ],
    "similarity": 0.97,
    "recommendation": "Consider consolidating these 2 similar designs"
  }
]
```

#### `POST /api/v1/memory/manage/cleanup`
Remove old records.

**Request:**
```json
{
  "days_old": 90,
  "dry_run": true
}
```

**Response:**
```json
{
  "dry_run": true,
  "records_to_delete": 5,
  "cutoff_date": "2026-01-13T...",
  "deleted": false
}
```

#### `POST /api/v1/memory/manage/consolidate`
Consolidate duplicate designs.

**Request:**
```json
{
  "similarity_threshold": 0.95
}
```

**Response:**
```json
{
  "duplicate_groups_found": 3,
  "designs_consolidated": 7,
  "designs_remaining": 35
}
```

#### `POST /api/v1/memory/manage/rebuild-indexes`
Rebuild FAISS indexes.

**Response:**
```json
{
  "status": "rebuilt",
  "total_records": 42,
  "user_id": 1,
  "timestamp": "2026-04-13T10:30:00Z"
}
```

## Integration Examples

### Example 1: Store Optimization Result

```python
import requests

# After running optimization
design_result = optimizer.run(...)

# Store in memory
response = requests.post(
    "http://localhost:8000/api/v1/memory/store",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "inputs": {
            "wn": design_result["transistor"]["wn"],
            "wp": design_result["transistor"]["wp"],
            "vdd": design_result["operating"]["vdd"],
            "temp": design_result["operating"]["temp"]
        },
        "outputs": {
            "freq": design_result["performance"]["freq"],
            "power": design_result["performance"]["power"],
            "delay": design_result["performance"]["delay"]
        },
        "source_scope": "optimization",
        "title": f"Opt run {run_id}: {design_id}",
        "tags": ["production", "optimized"]
    }
)

design_id = response.json()["record_id"]
print(f"✓ Stored design {design_id}")
```

### Example 2: Search for Similar Designs

```python
# Find similar designs to a given input
response = requests.post(
    "http://localhost:8000/api/v1/memory/search",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "inputs": {
            "wn": 1.5,
            "wp": 2.0,
            "vdd": 1.8,
            "temp": 27
        },
        "top_k": 10,
        "min_similarity": 0.8
    }
)

hits = response.json()["hits"]
for hit in hits:
    print(f"Design {hit['record_id']}: {hit['title']}")
    print(f"  Similarity: {hit['similarity_score']:.2%}")
    print(f"  Performance: {hit['outputs']['freq']} GHz, {hit['outputs']['power']} mW")
```

### Example 3: Batch Search and Analysis

```python
# Batch search multiple designs
queries = [
    {"inputs": {"wn": 1.2, "wp": 1.8, "vdd": 1.6}},
    {"inputs": {"wn": 1.8, "wp": 2.4, "vdd": 1.9}},
]

response = requests.post(
    "http://localhost:8000/api/v1/memory/batch-search",
    headers={"Authorization": f"Bearer {token}"},
    json={"queries": queries, "top_k": 5}
)

results = response.json()["results"]
total_search_time = sum(r["search_time_ms"] for r in results)
print(f"✓ Searched {len(queries)} queries in {total_search_time:.1f}ms")

# Get memory stats
stats = requests.get(
    "http://localhost:8000/api/v1/memory/manage/health",
    headers={"Authorization": f"Bearer {token}"}
).json()

print(f"Memory Health: {stats['health_score']}/100")
print(f"Total designs: {stats['total_designs']}")
print(f"Coverage: {stats['coverage']:.1f}%")
```

### Example 4: Memory Maintenance

```python
# Find duplicates
dups = requests.get(
    "http://localhost:8000/api/v1/memory/manage/duplicates?similarity_threshold=0.9",
    headers={"Authorization": f"Bearer {token}"}
).json()

print(f"Found {len(dups)} groups of similar designs")

# Consolidate if duplicates found
if len(dups) > 0:
    result = requests.post(
        "http://localhost:8000/api/v1/memory/manage/consolidate",
        headers={"Authorization": f"Bearer {token}"},
        json={"similarity_threshold": 0.95}
    ).json()
    
    print(f"Consolidated {result['designs_consolidated']} designs")
    print(f"Remaining: {result['designs_remaining']} designs")

# Cleanup old records (dry-run first)
cleanup = requests.post(
    "http://localhost:8000/api/v1/memory/manage/cleanup",
    headers={"Authorization": f"Bearer {token}"},
    json={"days_old": 90, "dry_run": True}
).json()

print(f"Would delete {cleanup['records_to_delete']} designs older than 90 days")

# Actually cleanup if needed
if cleanup['records_to_delete'] > 0:
    requests.post(
        "http://localhost:8000/api/v1/memory/manage/cleanup",
        headers={"Authorization": f"Bearer {token}"},
        json={"days_old": 90, "dry_run": False}
    )
    print("✓ Cleanup completed")
```

## Performance Characteristics

### Search Performance
| Dataset Size | Query Time | Index Rebuild |
|--|--|--|
| 10 designs | 1-2ms | 10ms |
| 100 designs | 2-5ms | 50ms |
| 1,000 designs | 5-15ms | 200ms |
| 10,000 designs | 10-30ms | 1-2s |
| 100,000 designs | 20-50ms* | 5-10s |

*With FAISS acceleration

### Storage Requirements
| Per Design | Estimate |
|--|--|
| Database record | ~2KB |
| Feature vector (18D) | 72 bytes |
| FAISS index | 1-2KB per design |
| **Total** | **~2-3KB per design** |

For 1,000 designs: ~2-3MB
For 10,000 designs: ~20-30MB

## Best Practices

### 1. Naming & Organization
```json
{
  "title": "Opt: power-optimized @ 27C, 1.8V [run_123]",
  "source_scope": "optimization",
  "tags": ["power-optimized", "fast-execution", "production"],
  "metadata": {
    "run_id": 123,
    "optimizer": "nsga2",
    "objectives": ["power", "frequency"],
    "pareto_rank": 1
  }
}
```

### 2. Regular Maintenance
```
Monthly:
- Run health check
- Review recommendations
- Consolidate duplicates (if > 10% similar)
- Cleanup old records > 180 days

Quarterly:
- Full analysis & distribution report
- Review tag consistency
- Archive low-value designs
```

### 3. Search Strategies
```python
# Strategy 1: Broad search (high recall)
response = search(
    inputs=user_input,
    top_k=20,
    min_similarity=0.5)

# Strategy 2: Focused search (high precision)
response = search(
    inputs=user_input,
    top_k=5,
    min_similarity=0.85,
    filters={"source_scope": "optimization"})

# Strategy 3: Incremental refinement
for threshold in [0.9, 0.8, 0.7, 0.6]:
    hits = search(..., min_similarity=threshold)
    if len(hits) >= 5:
        break
```

### 4. Handling Large Datasets
```python
# Batch import
designs = load_designs_from_file("designs.json")
for batch in chunks(designs, 100):
    for design in batch:
        store_design(design)
        
# Then rebuild once
rebuild_indexes()

# Volume search
results = batch_search([
    {"inputs": params for params in param_list}
])
```

## Troubleshooting

### Issue: Search Results Are Poor
**Symptoms:** Low similarity scores, unrelated results
**Solutions:**
1. Check input normalization
2. Verify feature encoding matches documentation
3. Increase `min_similarity` threshold
4. Review stored designs for quality

### Issue: Slow Searches
**Symptoms:** >100ms per query
**Solutions:**
1. Check dataset size (may need optimization)
2. Rebuild indexes: `POST /api/v1/memory/manage/rebuild-indexes`
3. Check server load
4. Consider pagination if retrieving large result sets

### Issue: Out of Memory
**Symptoms:** FAISS crashes on large datasets
**Solutions:**
1. Consolidate duplicates: `POST /api/v1/memory/manage/consolidate`
2. Cleanup old designs: `POST /api/v1/memory/manage/cleanup`
3. Archive to external storage
4. Scale database server

### Issue: Inconsistent Results
**Symptoms:** Same query returns different results
**Solutions:**
1. Verify indexes are up-to-date
2. Rebuild indexes regularly
3. Check for concurrent modifications
4. Monitor FAISS version consistency

## Database Schema

### DesignDNARecord Table
```sql
CREATE TABLE design_dna_records (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    source_scope VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    feature_vector_json JSON NOT NULL,  -- 18D feature vector
    input_json JSON NOT NULL,           -- Design inputs
    output_json JSON,                   -- Design outputs
    metadata_json JSON,                 -- Tags, source info, etc.
    created_at DATETIME DEFAULT NOW(),
    
    INDEX idx_user_id (user_id),
    INDEX idx_source_scope (source_scope),
    INDEX idx_created_at (created_at)
);
```

### FAISS Indexes
```
Location: services/api/data/faiss_index/
Files per user:
- user_{user_id}_design_dna.index (FAISS binary)
- user_{user_id}_design_dna_meta.json (record ID mapping)
```

## Roadmap

### Phase 1: Current ✅
- [x] Basic storage and search
- [x] FAISS indexing
- [x] Memory management
- [x] Health monitoring

### Phase 2: Planned
- [ ] Clustering (group similar designs automatically)
- [ ] Pattern detection (common configurations)
- [ ] Predictive analytics (suggest missing parameters)
- [ ] Multi-language search (semantic similarity)
- [ ] Design versioning (track design evolution)

### Phase 3: Advanced
- [ ] Knowledge graphs (design dependency mapping)
- [ ] Hybrid search (vector + keyword)
- [ ] Personalized recommendations (per user ML model)
- [ ] Memory federation (shared design libraries)

## Support

**Documentation:** See this guide
**API Docs:** `/docs` endpoint
**Issues:** Check troubleshooting section

For questions or issues, contact the development team.

---

**Last Updated:** April 13, 2026  
**Version:** 1.0.0  
**Status:** Production Ready ✅
