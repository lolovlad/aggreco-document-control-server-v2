from server.models.Object import PostObject
from server.tables import Object


def get_token(client):
    username = "admin@admin.com"
    password = "admin"

    response = client.post("/v1/login/sign-in", data={
        "grant_type": "",
        "username": username,
        "password": password,
        "client_id": "",
        "client_secret": ""
    },
                           headers={
                               'Content-Type': 'application/x-www-form-urlencoded',
                               'accept': 'application/json'
                           })
    return response.json()["access_token"]


async def test_add_object(client):
    token = get_token(client)

    obj = PostObject(
        name="Тестовое имя",
        address="Test address 2132131234",
        cx=123.23,
        cy=134.23,
        counterparty="OOO 'Тест'",
        id_state=1,
        description="lolol"
    )

    response = client.post("/v1/object", headers={"Authorization": f"Bearer {token}"},
                           json=obj.model_dump())
    assert response.status_code == 201


async def test_get_page(client):
    token = get_token(client)

    response = client.get("/v1/object/page", headers={"Authorization": f"Bearer {token}"})

    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1


async def test_all_object(client):
    token = get_token(client)

    response = client.get("/v1/object/list", headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1


async def test_delete_object(client):
    token = get_token(client)

    obj = PostObject(
        name="test_delete",
        address="test_delete",
        cx=123.23,
        cy=134.23,
        counterparty="test_delete",
        id_state=1,
        description="test_delete"
    )

    response = client.post("/v1/object", headers={"Authorization": f"Bearer {token}"},
                           json=obj.model_dump())

    response = client.get("/v1/object/list", headers={"Authorization": f"Bearer {token}"})
    data = [i for i in response.json() if i["name"] == "test_delete"][0]

    response = client.delete(f"/v1/object/{data['uuid']}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200

    response = client.get("/v1/object/list", headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert len(data) == 1


async def test_update_object(client):
    token = get_token(client)
    response = client.get("/v1/object/list", headers={"Authorization": f"Bearer {token}"})
    data = response.json()[0]

    data["counterparty"] = "test test test"
    response = client.put(f"/v1/object/{data['uuid']}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200

    response = client.get("/v1/object/list", headers={"Authorization": f"Bearer {token}"})
    data = response.json()[0]

    assert data["counterparty"] == "test test test"



