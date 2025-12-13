import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_experiment_statistics_basic(client: AsyncClient):
    exp_response = await client.post(
        "/api/experiments/",
        json={"name": "Stats Test Experiment", "description": "Test statistical analysis"}
    )
    assert exp_response.status_code == 200
    experiment = exp_response.json()
    experiment_id = experiment["id"]

    variant_response = await client.post(
        f"/api/experiments/{experiment_id}/variants",
        json={"name": "variant_a", "percent_allocated": 0.0}
    )
    assert variant_response.status_code == 200
    variant_a = variant_response.json()

    control_variant_id = None
    exp_detail = await client.get(f"/api/experiments/{experiment_id}")
    for variant in exp_detail.json()["variants"]:
        if variant["name"] == "control":
            control_variant_id = variant["id"]
            break

    user1 = await client.post("/api/users/", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@test.com"
    })
    assert user1.status_code == 200
    user1_id = user1.json()["id"]

    user2 = await client.post("/api/users/", json={
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@test.com"
    })
    assert user2.status_code == 200
    user2_id = user2.json()["id"]

    await client.post("/api/events/", json={
        "user_id": user1_id,
        "experiment_id": experiment_id,
        "variant_id": control_variant_id,
        "type": "page_view"
    })

    await client.post("/api/events/", json={
        "user_id": user1_id,
        "experiment_id": experiment_id,
        "variant_id": control_variant_id,
        "type": "conversion"
    })

    await client.post("/api/events/", json={
        "user_id": user2_id,
        "experiment_id": experiment_id,
        "variant_id": variant_a["id"],
        "type": "page_view"
    })

    stats_response = await client.post(
        f"/api/experiments/{experiment_id}/results",
        json={
            "conversion_event_type": "conversion",
            "confidence_level": 0.95,
            "significance_threshold": 0.05
        }
    )
    assert stats_response.status_code == 200
    stats = stats_response.json()

    assert stats["experiment_id"] == experiment_id
    assert stats["experiment_name"] == "Stats Test Experiment"
    assert stats["conversion_event_type"] == "conversion"
    assert len(stats["variants"]) == 2

    control_stats = next((v for v in stats["variants"] if v["is_control"]), None)
    assert control_stats is not None
    assert control_stats["total_users"] == 1
    assert control_stats["conversions"] == 1
    assert control_stats["conversion_rate"] == 100.0

    variant_a_stats = next((v for v in stats["variants"] if not v["is_control"]), None)
    assert variant_a_stats is not None
    assert variant_a_stats["total_users"] == 1
    assert variant_a_stats["conversions"] == 0
    assert variant_a_stats["conversion_rate"] == 0.0


@pytest.mark.asyncio
async def test_statistical_significance(client: AsyncClient):
    exp_response = await client.post(
        "/api/experiments/",
        json={"name": "Significance Test", "description": "Test p-values"}
    )
    assert exp_response.status_code == 200
    experiment = exp_response.json()
    experiment_id = experiment["id"]

    variant_response = await client.post(
        f"/api/experiments/{experiment_id}/variants",
        json={"name": "treatment", "percent_allocated": 0.0}
    )
    assert variant_response.status_code == 200
    treatment_variant = variant_response.json()

    exp_detail = await client.get(f"/api/experiments/{experiment_id}")
    control_variant_id = None
    for variant in exp_detail.json()["variants"]:
        if variant["name"] == "control":
            control_variant_id = variant["id"]
            break

    for i in range(10):
        user_response = await client.post("/api/users/", json={
            "first_name": "Control",
            "last_name": f"User{i}",
            "email": f"control{i}@test.com"
        })
        user_id = user_response.json()["id"]

        await client.post("/api/events/", json={
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant_id": control_variant_id,
            "type": "page_view"
        })

        if i < 5:
            await client.post("/api/events/", json={
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": control_variant_id,
                "type": "conversion"
            })

    for i in range(10):
        user_response = await client.post("/api/users/", json={
            "first_name": "Treatment",
            "last_name": f"User{i}",
            "email": f"treatment{i}@test.com"
        })
        user_id = user_response.json()["id"]

        await client.post("/api/events/", json={
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant_id": treatment_variant["id"],
            "type": "page_view"
        })

        if i < 8:
            await client.post("/api/events/", json={
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": treatment_variant["id"],
                "type": "conversion"
            })

    stats_response = await client.post(f"/api/experiments/{experiment_id}/results")
    assert stats_response.status_code == 200
    stats = stats_response.json()

    control_stats = next((v for v in stats["variants"] if v["is_control"]), None)
    assert control_stats["conversions"] == 5
    assert control_stats["total_users"] == 10
    assert control_stats["conversion_rate"] == 50.0

    treatment_stats = next((v for v in stats["variants"] if not v["is_control"]), None)
    assert treatment_stats["conversions"] == 8
    assert treatment_stats["total_users"] == 10
    assert treatment_stats["conversion_rate"] == 80.0
    assert treatment_stats["p_value"] is not None
    assert treatment_stats["relative_uplift"] == 60.0
    assert treatment_stats["confidence_interval"] is not None


@pytest.mark.asyncio
async def test_no_conversions(client: AsyncClient):
    exp_response = await client.post(
        "/api/experiments/",
        json={"name": "No Conversions Test", "description": "Test with no data"}
    )
    assert exp_response.status_code == 200
    experiment = exp_response.json()
    experiment_id = experiment["id"]

    stats_response = await client.post(f"/api/experiments/{experiment_id}/results")
    assert stats_response.status_code == 200
    stats = stats_response.json()

    assert len(stats["variants"]) == 1
    assert stats["variants"][0]["total_users"] == 0
    assert stats["variants"][0]["conversions"] == 0
    assert stats["variants"][0]["conversion_rate"] == 0.0
    assert stats["winner"] is None
