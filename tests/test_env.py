from server.models.User import Profession
from server.models.Equipment import PostTypeEquipment


def get_token(client):
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


async def test_get_type_user(client):
    token = get_token(client)
    response = client.get("/v1/env/type_user", headers={"Authorization": f"Bearer {token}"})

    data = response.json()
    assert len(data) == 3
    assert type(data) == list


async def test_add_profession(client):
    token = get_token(client)
    prof = Profession(
        name="junior_software_engineer"
    )
    response = client.post("/v1/env/profession", headers={"Authorization": f"Bearer {token}"},
                           json=prof.model_dump())
    assert response.status_code == 201


async def test_get_user_profession(client):
    token = get_token(client)
    response = client.get("/v1/env/profession",
                          headers={"Authorization": f"Bearer {token}"})

    assert len(response.json()) == 2
    assert response.status_code == 200


async def test_delete_profession(client):
    token = get_token(client)
    response = client.get("/v1/env/profession",
                          headers={"Authorization": f"Bearer {token}"})
    data = [i for i in response.json() if i["name"] != "unknown"][0]

    response = client.delete(f"/v1/env/profession/{data['id']}",
                             headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    response = client.get("/v1/env/profession",
                          headers={"Authorization": f"Bearer {token}"})
    assert len(response.json()) == 1


async def test_import_type_equip(client):
    token = get_token(client)
    response = client.post("/v1/env/type_equip/import_file", headers={
        "Authorization": f"Bearer {token}",
    },
                           files={"file": open("files/типы обарудованния.csv", "rb")})
    assert response.status_code == 201


async def test_add_type_equip(client):
    response = client.get("/v1/env/type_equip")
    data = response.json()
    old_type = len(data)
    token = get_token(client)
    type_equip = PostTypeEquipment(
        name="test_eqipment",
        code="1232414213231",
        description="Описание"
    )
    response = client.post("/v1/env/type_equip", headers={
        "Authorization": f"Bearer {token}",
    },
    json=type_equip.model_dump())

    response_data = client.get("/v1/env/type_equip")
    data = response_data.json()
    new_type = len(data)

    assert response.status_code == 201
    assert new_type - old_type == 1


#async def test_import_type_equip(client):
#    token = get_token(client)
#    response = client.post("/v1/env/type_equip/import_file", headers={
#        "Authorization": f"Bearer {token}",
#    },
#                           files={"file": open("files/типы обарудованния.csv", "rb")})
#    assert response.status_code == 201


async def test_get_type_equipment(client):
    response = client.get("/v1/env/type_equip")
    data = response.json()

    assert response.status_code == 200
    assert len(data) > 5


async def test_get_state_object(client):
    response = client.get("/v1/env/state_object")
    data = response.json()

    assert response.status_code == 200
    assert len(data) > 0


async def test_import_region(client):
    token = get_token(client)
    response = client.post("/v1/env/region/import_file", headers={
        "Authorization": f"Bearer {token}",
    },
                           files={"file": open("files/Регионы страны.csv", "rb")})
    assert response.status_code == 201


async def test_get_region(client):
    response = client.get("/v1/env/region/get_all")
    data = response.json()

    assert response.status_code == 200
    assert len(data) > 0


async def test_import_type_brake(client):
    token = get_token(client)
    response = client.post("/v1/env/type_brake/import_file", headers={
        "Authorization": f"Bearer {token}",
    },
                           files={"file": open("files/типы ошибки персонала (все ошибки).csv", "rb")})
    assert response.status_code == 201


async def test_get_type_brake(client):
    response = client.get("/v1/env/type_brake_mechanical/external_organizational")
    data = response.json()

    assert response.status_code == 200
    assert len(data) > 0

    response = client.get("/v1/env/type_brake_mechanical/meh")
    data = response.json()

    assert response.status_code == 200
    assert len(data) > 0

    response = client.get("/v1/env/type_brake_mechanical/domestic_organizational")
    data = response.json()

    assert response.status_code == 200
    assert len(data) > 0


async def test_import_signs_accident(client):
    token = get_token(client)
    response = client.post("/v1/env/signs_accident/import_file", headers={
        "Authorization": f"Bearer {token}",
    },
                           files={"file": open("files/Учетные признаки аварий.csv", "rb")})
    assert response.status_code == 201


async def test_get_signs_accident(client):
    response = client.get("/v1/env/region/get_all")
    data = response.json()

    assert response.status_code == 200
    assert len(data) > 0


async def test_get_type_event(client):
    response = client.get("/v1/env/event/type_event")
    data = response.json()
    assert response.status_code == 200
    assert len(data) > 0


async def test_get_state_event(client):
    response = client.get("/v1/env/event/state_event")
    data = response.json()
    assert response.status_code == 200
    assert len(data) > 0


async def test_get_state_claim(client):
    response = client.get("/v1/env/state_claim")
    data = response.json()
    assert response.status_code == 200
    assert len(data) > 0