import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSegmentsAPI:
    async def test_create_segment_with_rules(self, client: AsyncClient):
        """Test creating a segment with rules."""
        response = await client.post(
            "/api/segments/",
            json={
                "name": "premium_segment",
                "description": "A test segment",
                "rules": {"is_premium": True}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "premium_segment"
        assert data["description"] == "A test segment"
        assert data["rules"] == {"is_premium": True}
        assert "id" in data
        assert "created_at" in data


    async def test_get_segments(self, client: AsyncClient):
        for i in range(3):
            await client.post(
                "/api/segments/",
                json={"name": f"segment_{i}"}
            )

        response = await client.get("/api/segments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        

    async def test_get_segment_by_id(self, client: AsyncClient):
        create_response = await client.post(
            "/api/segments/",
            json={"name": "get_me_segment"}
        )
        segment_id = create_response.json()["id"]

        response = await client.get(f"/api/segments/{segment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == segment_id
        assert data["name"] == "get_me_segment"
        assert "users" in data


    async def test_update_segment(self, client: AsyncClient):
        create_response = await client.post(
            "/api/segments/",
            json={"name": "update_segment"}
        )
        segment_id = create_response.json()["id"]

        response = await client.put(
            f"/api/segments/{segment_id}",
            json={
                "name": "updated_segment",
                "description": "Updated description",
                "rules": {"country_code": "US"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated_segment"
        assert data["description"] == "Updated description"
        assert data["rules"] == {"country_code": "US"}
        

    async def test_assign_user_to_segment(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Assign",
                "last_name": "User",
                "email": "assign@example.com"
            }
        )
        user_id = user_response.json()["id"]

        segment_response = await client.post(
            "/api/segments/",
            json={"name": "assign_segment"}
        )
        segment_id = segment_response.json()["id"]

        response = await client.post(
            "/api/segments/assign-user",
            json={
                "user_id": user_id,
                "segment_id": segment_id
            }
        )
        assert response.status_code == 200
        assert response.json()["message"] == "User assigned to segment successfully"

        segment_detail = await client.get(f"/api/segments/{segment_id}")
        users = segment_detail.json()["users"]
        assert any(u["id"] == user_id for u in users)


    async def test_assign_segment_to_experiment(self, client: AsyncClient):
        segment_response = await client.post(
            "/api/segments/",
            json={"name": "exp_segment"}
        )
        segment_id = segment_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Test Experiment"}
        )
        exp_id = exp_response.json()["id"]

        response = await client.post(
            "/api/segments/assign-experiment",
            json={
                "experiment_id": exp_id,
                "segment_id": segment_id
            }
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Segment assigned to experiment successfully"

        exp_detail = await client.get(f"/api/experiments/{exp_id}")
        segments = exp_detail.json()["segments"]
        assert any(s["id"] == segment_id for s in segments)
