import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
class TestEventsAPI:
    async def test_create_event(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Exp",
                "last_name": "User",
                "email": "expuser@example.com"
            }
        )
        user_id = user_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Event Test Experiment"}
        )
        exp_id = exp_response.json()["id"]

        exp_detail = await client.get(f"/api/experiments/{exp_id}")
        variant_id = exp_detail.json()["variants"][0]["id"]

        response = await client.post(
            "/api/events/",
            json={
                "user_id": user_id,
                "experiment_id": exp_id,
                "variant_id": variant_id,
                "type": "conversion",
                "properties": {"value": 100}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["experiment_id"] == exp_id
        assert data["variant_id"] == variant_id
        assert data["type"] == "conversion"
        

    async def test_get_all_events(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Multi",
                "last_name": "Events",
                "email": "multi@example.com"
            }
        )
        user_id = user_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Events Test Experiment"}
        )
        exp_id = exp_response.json()["id"]

        for i in range(3):
            await client.post(
                "/api/events/",
                json={
                    "user_id": user_id,
                    "experiment_id": exp_id,
                    "type": f"event_{i}"
                }
            )

        response = await client.post(f"/api/events/{exp_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


    async def test_get_events_filtered_by_experiment(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Filter",
                "last_name": "User",
                "email": "filter@example.com"
            }
        )
        user_id = user_response.json()["id"]

        exp1_response = await client.post(
            "/api/experiments/",
            json={"name": "Experiment 1"}
        )
        exp1_id = exp1_response.json()["id"]

        exp2_response = await client.post(
            "/api/experiments/",
            json={"name": "Experiment 2"}
        )
        exp2_id = exp2_response.json()["id"]

        exp1_detail = await client.get(f"/api/experiments/{exp1_id}")
        variant1_id = exp1_detail.json()["variants"][0]["id"]

        exp2_detail = await client.get(f"/api/experiments/{exp2_id}")
        variant2_id = exp2_detail.json()["variants"][0]["id"]

        for i in range(2):
            await client.post(
                "/api/events/",
                json={
                    "user_id": user_id,
                    "experiment_id": exp1_id,
                    "variant_id": variant1_id,
                    "type": "exp1_event"
                }
            )

        for i in range(3):
            await client.post(
                "/api/events/",
                json={
                    "user_id": user_id,
                    "experiment_id": exp2_id,
                    "variant_id": variant2_id,
                    "type": "exp2_event"
                }
            )

        response = await client.post(f"/api/events/{exp1_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(e["experiment_id"] == exp1_id for e in data)

        response = await client.post(f"/api/events/{exp2_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(e["experiment_id"] == exp2_id for e in data)


    async def test_filter_events_by_variant(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Variant",
                "last_name": "Test",
                "email": "variant@example.com"
            }
        )
        user_id = user_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Variant Filter Test"}
        )
        exp_id = exp_response.json()["id"]

        exp_detail = await client.get(f"/api/experiments/{exp_id}")
        variant1_id = exp_detail.json()["variants"][0]["id"]

        await client.put(
            f"/api/experiments/{exp_id}/variants/{variant1_id}",
            json={"percent_allocated": 50.0}
        )

        variant2_response = await client.post(
            f"/api/experiments/{exp_id}/variants",
            json={"name": "variant_2", "percent_allocated": 50.0}
        )
        variant2_id = variant2_response.json()["id"]

        for i in range(3):
            await client.post(
                "/api/events/",
                json={
                    "user_id": user_id,
                    "experiment_id": exp_id,
                    "variant_id": variant1_id,
                    "type": "click"
                }
            )

        for i in range(2):
            await client.post(
                "/api/events/",
                json={
                    "user_id": user_id,
                    "experiment_id": exp_id,
                    "variant_id": variant2_id,
                    "type": "click"
                }
            )

        response = await client.post(
            f"/api/events/{exp_id}",
            json={"variant_id": variant1_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(e["variant_id"] == variant1_id for e in data)

        response = await client.post(
            f"/api/events/{exp_id}",
            json={"variant_id": variant2_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(e["variant_id"] == variant2_id for e in data)


    async def test_filter_events_by_event_types(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "EventType",
                "last_name": "Test",
                "email": "eventtype@example.com"
            }
        )
        user_id = user_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Event Type Filter Test"}
        )
        exp_id = exp_response.json()["id"]

        event_types = ["click", "view", "conversion", "scroll"]
        for event_type in event_types:
            for i in range(2):
                await client.post(
                    "/api/events/",
                    json={
                        "user_id": user_id,
                        "experiment_id": exp_id,
                        "type": event_type
                    }
                )

        response = await client.post(
            f"/api/events/{exp_id}",
            json={"event_types": ["click", "conversion"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert all(e["type"] in ["click", "conversion"] for e in data)

        response = await client.post(
            f"/api/events/{exp_id}",
            json={"event_types": ["view"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(e["type"] == "view" for e in data)


    async def test_filter_events_by_user_ids(self, client: AsyncClient):
        user_ids = []
        for i in range(3):
            user_response = await client.post(
                "/api/users/",
                json={
                    "first_name": f"User{i}",
                    "last_name": "Test",
                    "email": f"user{i}@example.com"
                }
            )
            user_ids.append(user_response.json()["id"])

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "User Filter Test"}
        )
        exp_id = exp_response.json()["id"]

        for user_id in user_ids:
            for i in range(2):
                await client.post(
                    "/api/events/",
                    json={
                        "user_id": user_id,
                        "experiment_id": exp_id,
                        "type": "click"
                    }
                )

        response = await client.post(
            f"/api/events/{exp_id}",
            json={"user_ids": [user_ids[0], user_ids[2]]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert all(e["user_id"] in [user_ids[0], user_ids[2]] for e in data)

        response = await client.post(
            f"/api/events/{exp_id}",
            json={"user_ids": [user_ids[1]]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(e["user_id"] == user_ids[1] for e in data)


    async def test_filter_events_by_time_range(self, client: AsyncClient):
        user_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Time",
                "last_name": "Test",
                "email": "time@example.com"
            }
        )
        user_id = user_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Time Filter Test"}
        )
        exp_id = exp_response.json()["id"]

        event_responses = []
        for i in range(5):
            response = await client.post(
                "/api/events/",
                json={
                    "user_id": user_id,
                    "experiment_id": exp_id,
                    "type": "click"
                }
            )
            event_responses.append(response.json())

        all_events_response = await client.post(f"/api/events/{exp_id}", json={})
        all_events = all_events_response.json()
        assert len(all_events) == 5

        timestamps = [datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) for e in all_events]
        timestamps.sort()

        mid_time = timestamps[2].isoformat()
        response = await client.post(
            f"/api/events/{exp_id}",
            json={"start_time": mid_time}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

        response = await client.post(
            f"/api/events/{exp_id}",
            json={"end_time": mid_time}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2


    async def test_filter_events_combined_filters(self, client: AsyncClient):

        user1_response = await client.post(
            "/api/users/",
            json={
                "first_name": "User1",
                "last_name": "Combined",
                "email": "user1combined@example.com"
            }
        )
        user1_id = user1_response.json()["id"]

        user2_response = await client.post(
            "/api/users/",
            json={
                "first_name": "User2",
                "last_name": "Combined",
                "email": "user2combined@example.com"
            }
        )
        user2_id = user2_response.json()["id"]

        exp_response = await client.post(
            "/api/experiments/",
            json={"name": "Combined Filter Test"}
        )
        exp_id = exp_response.json()["id"]

        exp_detail = await client.get(f"/api/experiments/{exp_id}")
        variant1_id = exp_detail.json()["variants"][0]["id"]

        await client.put(
            f"/api/experiments/{exp_id}/variants/{variant1_id}",
            json={"percent_allocated": 50.0}
        )

        variant2_response = await client.post(
            f"/api/experiments/{exp_id}/variants",
            json={"name": "variant_b", "percent_allocated": 50.0}
        )
        variant2_id = variant2_response.json()["id"]

        for i in range(2):
            await client.post(
                "/api/events/",
                json={
                    "user_id": user1_id,
                    "experiment_id": exp_id,
                    "variant_id": variant1_id,
                    "type": "click"
                }
            )

        await client.post(
            "/api/events/",
            json={
                "user_id": user1_id,
                "experiment_id": exp_id,
                "variant_id": variant1_id,
                "type": "conversion"
            }
        )

        for i in range(3):
            await client.post(
                "/api/events/",
                json={
                    "user_id": user2_id,
                    "experiment_id": exp_id,
                    "variant_id": variant2_id,
                    "type": "click"
                }
            )

        await client.post(
            "/api/events/",
            json={
                "user_id": user2_id,
                "experiment_id": exp_id,
                "variant_id": variant2_id,
                "type": "view"
            }
        )

        response = await client.post(
            f"/api/events/{exp_id}",
            json={
                "variant_id": variant1_id,
                "event_types": ["click"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(e["variant_id"] == variant1_id and e["type"] == "click" for e in data)

        response = await client.post(
            f"/api/events/{exp_id}",
            json={
                "user_ids": [user2_id],
                "variant_id": variant2_id,
                "event_types": ["click"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(
            e["user_id"] == user2_id and
            e["variant_id"] == variant2_id and
            e["type"] == "click"
            for e in data
        )

        response = await client.post(
            f"/api/events/{exp_id}",
            json={
                "user_ids": [user1_id, user2_id],
                "event_types": ["conversion", "view"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # 1 conversion from user1 + 1 view from user2
        assert all(e["type"] in ["conversion", "view"] for e in data)
