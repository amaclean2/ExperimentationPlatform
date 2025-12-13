import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthAPI:

    async def test_create_api_key(self, client_no_auth: AsyncClient):
        response = await client_no_auth.post(
            "/api/auth/keys",
            json={"name": "my_test_key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "my_test_key"
        assert "key" in data
        assert data["is_active"] is True
        assert "created_at" in data


    async def test_get_all_api_keys(self, client_no_auth: AsyncClient):
        await client_no_auth.post("/api/auth/keys", json={"name": "key1"})
        await client_no_auth.post("/api/auth/keys", json={"name": "key2"})

        response = await client_no_auth.get("/api/auth/keys")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all("name" in key for key in data)
        assert all("key" in key for key in data)


    async def test_delete_api_key(self, client_no_auth: AsyncClient):
        create_response = await client_no_auth.post(
            "/api/auth/keys",
            json={"name": "key_to_delete"}
        )
        key_id = create_response.json()["id"]

        delete_response = await client_no_auth.delete(f"/api/auth/keys/{key_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "API key deleted successfully"

        list_response = await client_no_auth.get("/api/auth/keys")
        remaining_keys = list_response.json()
        assert not any(key["id"] == key_id for key in remaining_keys)
