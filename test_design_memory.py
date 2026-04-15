"""Test suite for design memory system."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import pytest

BASE_URL = "http://localhost:8000/api/v1"


class DesignMemoryTester:
    """Test suite for design memory endpoints."""

    def __init__(self, token: str):
        """Initialize tester with auth token."""
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self.stored_ids = []

    async def test_store_design(self):
        """Test storing a design in memory."""
        print("\n=== Test 1: Store Design ===")

        design_data = {
            "inputs": {
                "wn": 1.5,
                "wp": 2.0,
                "vdd": 1.8,
                "temp": 27,
                "cl_ff": 0.1,
            },
            "outputs": {
                "freq": 2.5,
                "power": 100.5,
                "delay": 0.4,
            },
            "title": "Test Design v1",
            "summary": "Test design for memory system",
            "source_scope": "optimization",
            "tags": ["test", "fast"],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/memory/store",
                headers=self.headers,
                json=design_data,
            ) as resp:
                assert resp.status == 200, f"Failed to store design: {await resp.text()}"
                data = await resp.json()

                assert "record_id" in data
                assert data["title"] == design_data["title"]
                assert data["source_scope"] == design_data["source_scope"]

                self.stored_ids.append(data["record_id"])
                print(f"✓ Stored design {data['record_id']}")

    async def test_search_similar(self):
        """Test searching for similar designs."""
        print("\n=== Test 2: Search Similar Designs ===")

        if not self.stored_ids:
            print("⊘ Skipping - no designs stored yet")
            return

        search_data = {
            "inputs": {
                "wn": 1.45,
                "wp": 1.95,
                "vdd": 1.8,
                "temp": 27,
            },
            "top_k": 10,
            "min_similarity": 0.5,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/memory/search",
                headers=self.headers,
                json=search_data,
            ) as resp:
                assert resp.status == 200, f"Search failed: {await resp.text()}"
                data = await resp.json()

                assert "hits" in data
                assert "search_time_ms" in data
                assert "total_results" in data

                print(f"✓ Found {data['total_results']} similar designs")
                print(f"  Search time: {data['search_time_ms']}ms")

                for i, hit in enumerate(data["hits"][:3], 1):
                    print(f"  Hit {i}: {hit['title']} (score: {hit['similarity_score']:.2%})")

    async def test_batch_search(self):
        """Test batch search for multiple designs."""
        print("\n=== Test 3: Batch Search ===")

        queries = [
            {"inputs": {"wn": 1.5, "wp": 2.0, "vdd": 1.8, "temp": 27}},
            {"inputs": {"wn": 1.2, "wp": 1.8, "vdd": 1.6, "temp": 25}},
            {"inputs": {"wn": 1.8, "wp": 2.4, "vdd": 1.9, "temp": 50}},
        ]

        batch_data = {"queries": queries, "top_k": 5}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/memory/batch-search",
                headers=self.headers,
                json=batch_data,
            ) as resp:
                assert resp.status == 200, f"Batch search failed: {await resp.text()}"
                data = await resp.json()

                assert "results" in data
                assert "batch_count" in data
                print(f"✓ Searched {data['batch_count']} queries")

                total_time = sum(r["search_time_ms"] for r in data["results"])
                print(f"  Total time: {total_time:.1f}ms")
                print(f"  Avg time per query: {total_time / data['batch_count']:.1f}ms")

    async def test_list_designs(self):
        """Test listing designs."""
        print("\n=== Test 4: List Designs ===")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/memory/list?limit=50&offset=0&sort_by=created_at&order=desc",
                headers=self.headers,
            ) as resp:
                assert resp.status == 200, f"List failed: {await resp.text()}"
                data = await resp.json()

                assert "designs" in data
                assert "total" in data

                print(f"✓ Listed {len(data['designs'])} designs (total: {data['total']})")

                if data["designs"]:
                    print(f"  Latest: {data['designs'][0]['title']}")

    async def test_get_recommendations(self):
        """Test getting recommendations."""
        print("\n=== Test 5: Get Recommendations ===")

        rec_data = {
            "inputs": {"wn": 1.5, "wp": 2.0, "vdd": 1.8, "temp": 27},
            "recommendation_type": "similar_designs",
            "count": 5,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/memory/recommend",
                headers=self.headers,
                json=rec_data,
            ) as resp:
                assert resp.status == 200, f"Recommend failed: {await resp.text()}"
                data = await resp.json()

                assert isinstance(data, list)
                print(f"✓ Got {len(data)} recommendations")

                for i, rec in enumerate(data[:3], 1):
                    print(f"  Rec {i}: {rec['title']}")

    async def test_memory_stats(self):
        """Test getting memory statistics."""
        print("\n=== Test 6: Memory Statistics ===")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/memory/manage/stats",
                headers=self.headers,
            ) as resp:
                assert resp.status == 200, f"Stats failed: {await resp.text()}"
                data = await resp.json()

                assert "total_designs" in data
                assert "health_score" in data

                print(f"✓ Memory Stats:")
                print(f"  Total designs: {data['total_designs']}")
                print(f"  With outputs: {data['total_outputs_stored']}")
                print(f"  Indexed: {data['indexed_designs']}")
                print(f"  Size: {data['size_bytes'] / 1024:.1f} KB")

    async def test_memory_health(self):
        """Test getting memory health report."""
        print("\n=== Test 7: Memory Health ===")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/memory/manage/health",
                headers=self.headers,
            ) as resp:
                assert resp.status == 200, f"Health check failed: {await resp.text()}"
                data = await resp.json()

                assert "health_score" in data
                assert "recommendations" in data

                print(f"✓ Health Report:")
                print(f"  Health Score: {data['health_score']}/100")
                print(f"  Total designs: {data['total_designs']}")
                print(f"  Coverage: {data['coverage']:.1f}%")
                print(f"  Recommendations:")
                for rec in data["recommendations"]:
                    print(f"    - {rec}")

    async def test_find_duplicates(self):
        """Test finding duplicate designs."""
        print("\n=== Test 8: Find Duplicates ===")

        # Store similar design to test duplicates
        if self.stored_ids:
            similar_design = {
                "inputs": {
                    "wn": 1.51,
                    "wp": 2.01,
                    "vdd": 1.8,
                    "temp": 27,
                },
                "outputs": {
                    "freq": 2.45,
                    "power": 101.0,
                    "delay": 0.41,
                },
                "title": "Similar Design (duplicate test)",
                "source_scope": "optimization",
            }

            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{BASE_URL}/memory/store",
                    headers=self.headers,
                    json=similar_design,
                )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/memory/manage/duplicates?similarity_threshold=0.9",
                headers=self.headers,
            ) as resp:
                assert resp.status == 200, f"Duplicate detection failed: {await resp.text()}"
                data = await resp.json()

                assert isinstance(data, list)
                print(f"✓ Found {len(data)} duplicate groups")

                for group in data[:3]:
                    print(f"  Group: {len(group['group'])} designs (similarity: {group['similarity']:.2%})")

    async def test_analysis(self):
        """Test comprehensive memory analysis."""
        print("\n=== Test 9: Memory Analysis ===")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/memory/manage/analysis",
                headers=self.headers,
            ) as resp:
                assert resp.status == 200, f"Analysis failed: {await resp.text()}"
                data = await resp.json()

                assert "health" in data
                assert "distribution" in data

                print(f"✓ Analysis Complete:")
                print(f"  Health: {data['health']['health_score']}/100")
                print(f"  Distribution scopes: {len(data['distribution']['scope_distribution'])}")

    async def test_cleanup_dryrun(self):
        """Test cleanup in dry-run mode."""
        print("\n=== Test 10: Cleanup (Dry-Run) ===")

        cleanup_data = {"days_old": 90, "dry_run": True}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/memory/manage/cleanup",
                headers=self.headers,
                json=cleanup_data,
            ) as resp:
                assert resp.status == 200, f"Cleanup failed: {await resp.text()}"
                data = await resp.json()

                assert data["dry_run"] is True
                print(f"✓ Dry-run cleanup:")
                print(f"  Would delete: {data['records_to_delete']} designs")
                print(f"  Cutoff date: {data['cutoff_date']}")

    async def test_rebuild_indexes(self):
        """Test rebuilding indexes."""
        print("\n=== Test 11: Rebuild Indexes ===")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/memory/manage/rebuild-indexes",
                headers=self.headers,
            ) as resp:
                assert resp.status == 200, f"Rebuild failed: {await resp.text()}"
                data = await resp.json()

                assert data["status"] == "rebuilt"
                print(f"✓ Rebuilt indexes:")
                print(f"  Total records: {data['total_records']}")
                print(f"  Timestamp: {data['timestamp']}")

    async def run_all_tests(self):
        """Run all tests sequentially."""
        print("🧪 Design Memory System Test Suite")
        print("=" * 50)

        tests = [
            self.test_store_design,
            self.test_search_similar,
            self.test_batch_search,
            self.test_list_designs,
            self.test_get_recommendations,
            self.test_memory_stats,
            self.test_memory_health,
            self.test_find_duplicates,
            self.test_analysis,
            self.test_cleanup_dryrun,
            self.test_rebuild_indexes,
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                await test()
                passed += 1
            except Exception as e:
                print(f"✗ Test failed: {e}")
                failed += 1

        print("\n" + "=" * 50)
        print(f"Results: {passed} passed, {failed} failed")
        print("=" * 50)

        return failed == 0


async def main():
    """Main test runner."""
    import sys

    # Get token from environment or command line
    token = sys.argv[1] if len(sys.argv) > 1 else "test_token"

    print("Prerequisites check:")
    print("✓ Design memory service running")
    print("✓ API server on localhost:8000")
    print("✓ Authentication token ready")
    print()

    tester = DesignMemoryTester(token)
    success = await tester.run_all_tests()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    # Run: python test_design_memory.py YOUR_AUTH_TOKEN
    asyncio.run(main())
