import json
import pytest
from server.models.User import UserPost, UserUpdate, Profession


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


def get_token_superuser(client):
    username = "super_admin@super_admin.com"
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


async def test_create_user(client):
    token = get_token(client)
    user = UserPost(
        email="test@test.ru",
        id_type=3,
        name="test",
        surname="test",
        patronymic="test",
        id_profession=None,
        password="test"
    )
    response = client.post("/v1/user", headers={"Authorization": f"Bearer {token}"},
                           json=user.model_dump())
    assert response.status_code == 201


async def test_search_user(client):
    token = get_token(client)
    response = client.get("/v1/user/search", params={"search_field": "tes"}, headers={"Authorization": f"Bearer {token}"},)
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "test@test.ru"


async def test_user_login(client):
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
    assert len(response.json()["access_token"]) > 10

    username = "super_admin@super_admin.com"
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
    assert len(response.json()["access_token"]) > 10


async def test_get_user(client):

    cl = client

    token = get_token(cl)

    resp = client.get("/v1/user/page_user")
    assert resp.status_code == 401

    resp = client.get("/v1/user/page_user", headers={
        "Authorization": f"Bearer {token}"
    })
    assert resp.status_code == 200
    assert len(resp.json()) == 4

    cl = client

    token = get_token_superuser(cl)

    resp = client.get("/v1/user/page_user", headers={
        "Authorization": f"Bearer {token}"
    })
    assert resp.status_code == 200


async def test_update_user(client):
    token = get_token(client)
    response = client.get("/v1/user/search", params={"search_field": "tes"}, headers={"Authorization": f"Bearer {token}"},)

    data = response.json()[0]

    user_update = UserUpdate.model_validate(data)

    user_update.email = "test1@test1.ru"

    response = client.put(f"/v1/user/{data['uuid']}", headers={"Authorization": f"Bearer {token}"}, json=user_update.model_dump())
    assert response.status_code == 205


async def test_delete_user(client):
    token = get_token(client)
    response = client.get("/v1/user/search", params={"search_field": "tes"},
                          headers={"Authorization": f"Bearer {token}"}, )

    data = response.json()[0]
    response = client.delete(f"/v1/user/{data['uuid']}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


async def test_update_profile(client):
    token = get_token(client)
    response = client.get("/v1/user/search", params={"search_field": "tes"}, headers={"Authorization": f"Bearer {token}"},)

    data = response.json()[0]

    user_update = UserUpdate.model_validate(data)

    user_update.email = "test1@test1.ru"

    response = client.put(f"/v1/user/profile/update/{data['uuid']}", headers={"Authorization": f"Bearer {token}"}, json=user_update.model_dump())
    assert response.status_code == 406
    response = client.get("/v1/user/search", params={"search_field": "admin admin admin"},
                          headers={"Authorization": f"Bearer {token}"}, )

    data = response.json()[0]

    user_update = UserUpdate.model_validate(data)
    user_update.patronymic = "admin1"
    response = client.put(f"/v1/user/profile/update/{data['uuid']}", headers={"Authorization": f"Bearer {token}"},
                          json=user_update.model_dump())
    assert response.status_code == 205
