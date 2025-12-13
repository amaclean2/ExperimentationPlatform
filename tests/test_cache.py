import pytest
from httpx import AsyncClient
from src.cache import (
    experiment_cache, segment_cache,
    clear_all_caches, invalidate_experiment_cache, invalidate_segment_cache
)


@pytest.mark.asyncio
async def test_experiment_caching(client: AsyncClient):
    clear_all_caches()

    exp_response = await client.post(
        "/api/experiments/",
        json={"name": "Cache Test Experiment", "description": "Test caching"}
    )
    assert exp_response.status_code == 200
    experiment_id = exp_response.json()["id"]

    assert len(experiment_cache) == 0

    get_response1 = await client.get(f"/api/experiments/{experiment_id}")
    assert get_response1.status_code == 200

    cache_size_after_first_get = len(experiment_cache)
    assert cache_size_after_first_get > 0

    get_response2 = await client.get(f"/api/experiments/{experiment_id}")
    assert get_response2.status_code == 200
    assert get_response1.json() == get_response2.json()

    assert len(experiment_cache) == cache_size_after_first_get


@pytest.mark.asyncio
async def test_experiment_cache_invalidation_on_variant_create(client: AsyncClient):
    clear_all_caches()

    exp_response = await client.post(
        "/api/experiments/",
        json={"name": "Cache Invalidation Test", "description": "Test cache invalidation"}
    )
    assert exp_response.status_code == 200
    experiment_id = exp_response.json()["id"]

    get_response1 = await client.get(f"/api/experiments/{experiment_id}")
    assert get_response1.status_code == 200
    variants_before = get_response1.json()["variants"]

    cache_size_before = len(experiment_cache)
    assert cache_size_before > 0

    variant_response = await client.post(
        f"/api/experiments/{experiment_id}/variants",
        json={"name": "new_variant", "percent_allocated": 0.0}
    )
    assert variant_response.status_code == 200

    get_response2 = await client.get(f"/api/experiments/{experiment_id}")
    assert get_response2.status_code == 200
    variants_after = get_response2.json()["variants"]

    assert len(variants_after) > len(variants_before)


@pytest.mark.asyncio
async def test_experiment_cache_invalidation_on_variant_update(client: AsyncClient):
    clear_all_caches()

    exp_response = await client.post(
        "/api/experiments/",
        json={"name": "Update Cache Test", "description": "Test cache on update"}
    )
    assert exp_response.status_code == 200
    experiment_id = exp_response.json()["id"]

    control_update = await client.put(
        f"/api/experiments/{experiment_id}/variants/1",
        json={"percent_allocated": 50.0}
    )

    variant_response = await client.post(
        f"/api/experiments/{experiment_id}/variants",
        json={"name": "test_variant", "percent_allocated": 50.0}
    )
    assert variant_response.status_code == 200
    variant_id = variant_response.json()["id"]

    get_response1 = await client.get(f"/api/experiments/{experiment_id}")
    assert get_response1.status_code == 200

    update_response = await client.put(
        f"/api/experiments/{experiment_id}/variants/{variant_id}",
        json={"name": "updated_variant"}
    )
    assert update_response.status_code == 200

    get_response2 = await client.get(f"/api/experiments/{experiment_id}")
    assert get_response2.status_code == 200

    updated_variant = next(
        (v for v in get_response2.json()["variants"] if v["id"] == variant_id),
        None
    )
    assert updated_variant is not None
    assert updated_variant["name"] == "updated_variant"


@pytest.mark.asyncio
async def test_segment_caching(client: AsyncClient):
    clear_all_caches()

    segment_response = await client.post(
        "/api/segments/",
        json={
            "name": "Cache Test Segment",
            "description": "Test segment caching",
            "rules": {"is_premium": True}
        }
    )
    assert segment_response.status_code == 200
    segment_id = segment_response.json()["id"]

    assert len(segment_cache) == 0

    get_response1 = await client.get(f"/api/segments/{segment_id}")
    assert get_response1.status_code == 200

    cache_size_after_first_get = len(segment_cache)
    assert cache_size_after_first_get > 0

    get_response2 = await client.get(f"/api/segments/{segment_id}")
    assert get_response2.status_code == 200
    assert get_response1.json() == get_response2.json()

    assert len(segment_cache) == cache_size_after_first_get


@pytest.mark.asyncio
async def test_segment_cache_invalidation_on_update(client: AsyncClient):
    clear_all_caches()

    segment_response = await client.post(
        "/api/segments/",
        json={
            "name": "Segment Update Cache Test",
            "description": "Original description",
            "rules": {"is_premium": True}
        }
    )
    assert segment_response.status_code == 200
    segment_id = segment_response.json()["id"]

    get_response1 = await client.get(f"/api/segments/{segment_id}")
    assert get_response1.status_code == 200
    assert get_response1.json()["description"] == "Original description"

    cache_size = len(segment_cache)
    assert cache_size > 0

    update_response = await client.put(
        f"/api/segments/{segment_id}",
        json={"description": "Updated description"}
    )
    assert update_response.status_code == 200

    get_response2 = await client.get(f"/api/segments/{segment_id}")
    assert get_response2.status_code == 200
    assert get_response2.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_segment_cache_invalidation_on_user_assignment(client: AsyncClient):
    clear_all_caches()

    segment_response = await client.post(
        "/api/segments/",
        json={"name": "User Assignment Cache Test", "description": "Test"}
    )
    assert segment_response.status_code == 200
    segment_id = segment_response.json()["id"]

    get_response1 = await client.get(f"/api/segments/{segment_id}")
    assert get_response1.status_code == 200

    cache_size_before = len(segment_cache)
    assert cache_size_before > 0

    update_response = await client.put(
        f"/api/segments/{segment_id}",
        json={"name": "User Assignment Cache Test Updated"}
    )
    assert update_response.status_code == 200

    get_response2 = await client.get(f"/api/segments/{segment_id}")
    assert get_response2.status_code == 200
    assert get_response2.json()["name"] == "User Assignment Cache Test Updated"


