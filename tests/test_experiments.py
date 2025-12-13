import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestExperimentsAPI:
    async def test_create_experiment(self, client: AsyncClient):
        response = await client.post(
            "/api/experiments/",
            json={
                "name": "Auto Control Test",
                "description": "A test experiment"
            }
        )
        assert response.status_code == 200
        experiment_id = response.json()["id"]

        detail_response = await client.get(f"/api/experiments/{experiment_id}")
        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["name"] == "Auto Control Test"
        assert data["description"] == "A test experiment"
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data

        assert len(data["variants"]) == 1
        assert data["variants"][0]["name"] == "control"
        assert data["variants"][0]["percent_allocated"] == 100.0


    async def test_get_experiments(self, client: AsyncClient):
        for i in range(3):
            await client.post(
                "/api/experiments/",
                json={"name": f"Experiment {i}"}
            )

        response = await client.get("/api/experiments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        

    async def test_get_experiment_by_id(self, client: AsyncClient):
        create_response = await client.post(
            "/api/experiments/",
            json={"name": "Get Me Experiment"}
        )
        exp_id = create_response.json()["id"]

        response = await client.get(f"/api/experiments/{exp_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == exp_id
        assert data["name"] == "Get Me Experiment"
        assert "variants" in data
        assert "segments" in data


    async def test_create_variant(self, client: AsyncClient):
        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Variant Test Experiment"}
        )
        exp_id = exp_response.json()["id"]

        exp_detail = await client.get(f"/api/experiments/{exp_id}")
        control_variant_id = exp_detail.json()["variants"][0]["id"]

        await client.put(
            f"/api/experiments/{exp_id}/variants/{control_variant_id}",
            json={"percent_allocated": 50.0}
        )

        response = await client.post(
            f"/api/experiments/{exp_id}/variants",
            json={
                "name": "variant_a",
                "percent_allocated": 50.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "variant_a"
        assert data["percent_allocated"] == 50.0
        assert data["experiment_id"] == exp_id
        

    async def test_update_variant(self, client: AsyncClient):
        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Update Variant Test"}
        )
        exp_id = exp_response.json()["id"]

        exp_detail = await client.get(f"/api/experiments/{exp_id}")
        variant_id = exp_detail.json()["variants"][0]["id"]

        response = await client.put(
            f"/api/experiments/{exp_id}/variants/{variant_id}",
            json={
                "name": "updated_control",
                "percent_allocated": 75.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated_control"
        assert data["percent_allocated"] == 75.0


    async def test_check_user_eligibility_no_segments(self, client: AsyncClient):

        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com"
            }
        )
        user_id = user_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "No Segment Experiment"}
        )
        exp_id = exp_response.json()["id"]

        response = await client.post(
            "/api/experiments/check-eligibility",
            json={
                "user_id": user_id,
                "experiment_ids": [exp_id]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert str(exp_id) in data["eligible_experiment_ids"]
        assert "variant_id" in data["eligible_experiment_ids"][str(exp_id)]

    async def test_check_user_eligibility_with_manual_segment_assignment(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Segment",
                "last_name": "User",
                "email": "segment@example.com"
            }
        )
        user_id = user_response.json()["id"]

        segment_response = await client.post(
            "/api/segments/",
            json={"name": "premium_users"}
        )
        segment_id = segment_response.json()["id"]

        await client.post(
            "/api/segments/assign-user",
            json={"user_id": user_id, "segment_id": segment_id}
        )

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Segment Experiment"}
        )
        exp_id = exp_response.json()["id"]

        await client.post(
            "/api/segments/assign-experiment",
            json={"experiment_id": exp_id, "segment_id": segment_id}
        )

        response = await client.post(
            "/api/experiments/check-eligibility",
            json={
                "user_id": user_id,
                "experiment_ids": [exp_id]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert str(exp_id) in data["eligible_experiment_ids"]


    async def test_check_user_eligibility_with_rule_based_segment(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Premium",
                "last_name": "User",
                "email": "premium@example.com",
                "is_premium": True
            }
        )
        user_id = user_response.json()["id"]

        segment_response = await client.post(
            "/api/segments/",
            json={
                "name": "premium_segment",
                "rules": {"is_premium": True}
            }
        )
        segment_id = segment_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Premium Experiment"}
        )
        exp_id = exp_response.json()["id"]

        await client.post(
            "/api/segments/assign-experiment",
            json={"experiment_id": exp_id, "segment_id": segment_id}
        )

        response = await client.post(
            "/api/experiments/check-eligibility",
            json={
                "user_id": user_id,
                "experiment_ids": [exp_id]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert str(exp_id) in data["eligible_experiment_ids"]


    async def test_check_user_eligibility_not_in_segment(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Regular",
                "last_name": "User",
                "email": "regular@example.com",
                "is_premium": False
            }
        )
        user_id = user_response.json()["id"]

        segment_response = await client.post(
            "/api/segments/",
            json={
                "name": "premium_only",
                "rules": {"is_premium": True}
            }
        )
        segment_id = segment_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Premium Only Experiment"}
        )
        exp_id = exp_response.json()["id"]

        await client.post(
            "/api/segments/assign-experiment",
            json={"experiment_id": exp_id, "segment_id": segment_id}
        )

        response = await client.post(
            "/api/experiments/check-eligibility",
            json={
                "user_id": user_id,
                "experiment_ids": [exp_id]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert str(exp_id) not in data["eligible_experiment_ids"]
        

    async def test_check_eligibility_consistent_variant_assignment(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Consistent",
                "last_name": "User",
                "email": "consistent@example.com"
            }
        )
        user_id = user_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Consistency Test"}
        )
        exp_id = exp_response.json()["id"]

        responses = []
        for _ in range(5):
            response = await client.post(
                "/api/experiments/check-eligibility",
                json={
                    "user_id": user_id,
                    "experiment_ids": [exp_id]
                }
            )
            responses.append(response.json())

        variant_ids = [
            resp["eligible_experiment_ids"][str(exp_id)]["variant_id"]
            for resp in responses
        ]
        assert all(vid == variant_ids[0] for vid in variant_ids)
