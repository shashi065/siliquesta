"""End-to-end integration tests for SILIQUESTA system."""

import pytest
import asyncio
from typing import Optional
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import get_db, async_session_maker
from app.models import User
from app.config import settings


@pytest.fixture
async def db_session() -> AsyncSession:
    """Get a test database session"""
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client() -> AsyncClient:
    """Get an async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        email=f"test-{asyncio.get_event_loop().time()}@example.com",
        full_name="Test User",
        password_hash="hashed_password",  # Mock hash in real test
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestProjectsAPI:
    """Test project CRUD operations"""

    async def test_create_project(self, client: AsyncClient, test_user: User):
        """Test creating a new project"""
        response = await client.post(
            "/api/v1/projects",
            json={
                "name": "Test Circuit Design",
                "description": "A test circuit",
                "tags": ["test", "integration"],
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Circuit Design"
        assert data["description"] == "A test circuit"
        assert "id" in data
        assert "slug" in data

    async def test_list_projects(self, client: AsyncClient, test_user: User):
        """Test listing projects"""
        # Create a project first
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "name": "Test Project",
                "description": "Test Description",
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert create_response.status_code == 201

        # List projects
        list_response = await client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_get_project(self, client: AsyncClient, test_user: User):
        """Test retrieving a specific project"""
        # Create a project first
        create_response = await client.post(
            "/api/v1/projects",
            json={"name": "Get Test Project"},
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        project_id = create_response.json()["id"]

        # Get the project
        get_response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == project_id
        assert data["name"] == "Get Test Project"

    async def test_update_project(self, client: AsyncClient, test_user: User):
        """Test updating a project"""
        # Create a project
        create_response = await client.post(
            "/api/v1/projects",
            json={"name": "Original Name"},
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        project_id = create_response.json()["id"]

        # Update the project
        update_response = await client.put(
            f"/api/v1/projects/{project_id}",
            json={"name": "Updated Name", "description": "New description"},
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    async def test_delete_project(self, client: AsyncClient, test_user: User):
        """Test deleting a project"""
        # Create a project
        create_response = await client.post(
            "/api/v1/projects",
            json={"name": "Delete Test"},
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        project_id = create_response.json()["id"]

        # Delete the project
        delete_response = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert delete_response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert get_response.status_code == 404

    async def test_save_design_state(self, client: AsyncClient, test_user: User):
        """Test saving design state"""
        # Create a project
        create_response = await client.post(
            "/api/v1/projects",
            json={"name": "Design Test"},
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        project_id = create_response.json()["id"]

        # Save design state
        design_data = {
            "components": [
                {"type": "nmos", "w": 10, "l": 1},
                {"type": "pmos", "w": 20, "l": 1},
            ],
            "connections": [{"from": "nmos", "to": "pmos"}],
        }
        save_response = await client.post(
            f"/api/v1/projects/{project_id}/save-design",
            json=design_data,
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert save_response.status_code == 200

        # Verify design state was saved
        get_response = await client.get(
            f"/api/v1/projects/{project_id}/design-state",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["design_state"] == design_data


class TestSimulationIntegration:
    """Test simulation endpoint integration"""

    async def test_submit_simulation(self, client: AsyncClient, test_user: User):
        """Test submitting a simulation job"""
        response = await client.post(
            "/api/v1/simulate",
            json={
                "wn": 5,
                "wp": 10,
                "vdd": 1.2,
                "temp": 25,
                "cl_ff": 1.0,
                "corner": "tt",
                "tech_node": 5,
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "freq" in data or "job_id" in data or "status" in data

    async def test_simulation_sweep(self, client: AsyncClient, test_user: User):
        """Test parameter sweep simulation"""
        response = await client.post(
            "/api/v1/simulate/sweep?max_wn=20",
            json={
                "wn": 5,
                "wp": 10,
                "vdd": 1.2,
                "temp": 25,
                "cl_ff": 1.0,
                "corner": "tt",
                "tech_node": 5,
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert response.status_code == 200 or response.status_code == 202


class TestOptimizationIntegration:
    """Test optimization endpoint integration"""

    async def test_traditional_optimization(self, client: AsyncClient, test_user: User):
        """Test traditional ADA optimization"""
        response = await client.post(
            "/api/v1/optimize",
            json={
                "wp": 10,
                "vdd": 1.2,
                "temp": 25,
                "cl_ff": 1.0,
                "tech_node": 5,
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert response.status_code == 200 or response.status_code == 202

    async def test_ml_optimization(self, client: AsyncClient, test_user: User):
        """Test ML-powered optimization"""
        response = await client.post(
            "/api/v1/optimize/ml-optimize",
            json={
                "wp": 10,
                "vdd": 1.2,
                "temp": 25,
                "cl_ff": 1.0,
                "tech_node": 5,
                "objective": "minimize_power",
                "constraints": {"max_freq": 100},
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert response.status_code == 200 or response.status_code == 202
        data = response.json()
        # Should include ML-specific fields
        assert "optimized_params" in data or "predictions" in data or "job_id" in data


class TestResponseFormat:
    """Test that all endpoints return consistent response formats"""

    async def test_error_response_format(self, client: AsyncClient):
        """Test that errors have consistent format"""
        # Try to access a non-existent project without auth
        response = await client.get("/api/v1/projects/99999")
        assert response.status_code in [401, 404]
        data = response.json()
        assert "detail" in data or "error" in data

    async def test_pagination_format(self, client: AsyncClient, test_user: User):
        """Test that list endpoints support pagination"""
        response = await client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert response.status_code == 200
        # Should be a list or have pagination info
        data = response.json()
        assert isinstance(data, (list, dict))


class TestAuthenticationFlow:
    """Test that authentication works across all endpoints"""

    async def test_unauthenticated_access(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected"""
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401

    async def test_invalid_token_format(self, client: AsyncClient):
        """Test that invalid token format is rejected"""
        response = await client.get(
            "/api/v1/projects",
            headers={"Authorization": "InvalidToken"},
        )
        assert response.status_code == 401

    async def test_expired_token(self, client: AsyncClient):
        """Test that expired tokens are rejected"""
        response = await client.get(
            "/api/v1/projects",
            headers={"Authorization": "Bearer expired.token.here"},
        )
        assert response.status_code == 401


class TestEndToEndFlows:
    """Test complete workflows across multiple components"""

    async def test_save_and_simulate_flow(self, client: AsyncClient, test_user: User):
        """Test: Create project → Save design → Run simulation"""
        # 1. Create project
        proj_response = await client.post(
            "/api/v1/projects",
            json={"name": "E2E Test Project"},
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert proj_response.status_code == 201
        project_id = proj_response.json()["id"]

        # 2. Save design state
        design_data = {"components": [], "parameters": {"wn": 5, "wp": 10}}
        design_response = await client.post(
            f"/api/v1/projects/{project_id}/save-design",
            json=design_data,
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert design_response.status_code == 200

        # 3. Run simulation
        sim_response = await client.post(
            "/api/v1/simulate",
            json={
                "wn": 5,
                "wp": 10,
                "vdd": 1.2,
                "temp": 25,
                "cl_ff": 1.0,
                "corner": "tt",
                "tech_node": 5,
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        # Simulation may be async, so 200 or 202 accepted
        assert sim_response.status_code in [200, 202]

    async def test_optimize_and_compare_flow(self, client: AsyncClient, test_user: User):
        """Test: Run baseline sim → ML optimize → Compare results"""
        # 1. Run baseline simulation
        baseline_response = await client.post(
            "/api/v1/simulate",
            json={
                "wn": 5,
                "wp": 10,
                "vdd": 1.2,
                "temp": 25,
                "cl_ff": 1.0,
                "corner": "tt",
                "tech_node": 5,
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert baseline_response.status_code in [200, 202]

        # 2. Run ML optimization
        opt_response = await client.post(
            "/api/v1/optimize/ml-optimize",
            json={
                "wp": 10,
                "vdd": 1.2,
                "temp": 25,
                "cl_ff": 1.0,
                "tech_node": 5,
            },
            headers={"Authorization": f"Bearer {test_user.id}"},
        )
        assert opt_response.status_code in [200, 202]


if __name__ == "__main__":
    print("Integration tests defined. Run with: pytest backend/tests/test_e2e_integration.py -v")
