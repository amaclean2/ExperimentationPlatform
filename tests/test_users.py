import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUsersAPI:
    async def test_create_user(self, client: AsyncClient):
        response = await client.post(
            "/api/users/",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "is_premium": False,
                "country_code": "US"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["is_premium"] is False
        assert data["country_code"] == "US"
        assert "id" in data
        assert "created_at" in data


    async def test_get_users(self, client: AsyncClient):
        for i in range(3):
            await client.post(
                "/api/users/",
                json={
                    "first_name": f"User{i}",
                    "last_name": "Test",
                    "email": f"user{i}@example.com"
                }
            )

        response = await client.get("/api/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    async def test_get_user_by_id(self, client: AsyncClient):
        create_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Get",
                "last_name": "Me",
                "email": "getme@example.com"
            }
        )
        user_id = create_response.json()["id"]

        response = await client.get(f"/api/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "getme@example.com"


    async def test_update_user(self, client: AsyncClient):
        create_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Update",
                "last_name": "Me",
                "email": "updateme@example.com",
                "is_premium": False
            }
        )
        user_id = create_response.json()["id"]

        response = await client.put(
            f"/api/users/{user_id}",
            json={
                "first_name": "Updated",
                "is_premium": True,
                "country_code": "CA"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["is_premium"] is True
        assert data["country_code"] == "CA"
        assert data["last_name"] == "Me"


    async def test_delete_user(self, client: AsyncClient):
        create_response = await client.post(
            "/api/users/",
            json={
                "first_name": "Delete",
                "last_name": "Me",
                "email": "deleteme@example.com"
            }
        )
        user_id = create_response.json()["id"]

        response = await client.delete(f"/api/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"

        get_response = await client.get(f"/api/users/{user_id}")
        assert get_response.status_code == 404


    async def test_authentication_required(self, client_no_auth: AsyncClient):
        response = await client_no_auth.get("/api/users/")
        assert response.status_code == 401
