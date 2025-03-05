from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient
from typing import Generator, Any
from server.main import app
from server.database import get_session
from server.tables import base
import asyncio
import pytest
from server.tables import (User,
                           TypeUser,
                           StateObject,
                           TypeEquipment,
                           ClassBrake,
                           TypeEvent,
                           StateEvent,
                           Profession,
                           StateAccident,
                           StateClaim)
from sqlalchemy import select, func
from pytest_asyncio import is_async_test


URL_DATABASE = f"postgresql+asyncpg://admin_test:admin_test@localhost:" \
               f"5433/document_test"


test_engine = create_async_engine(URL_DATABASE, echo=False, future=True)
async_session_test = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


ClEAN_TABLE = [
    "user"
]


async def get_session_test() -> AsyncSession:
    async with async_session_test() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="session")
async def async_session_test_fixture() -> sessionmaker:
    engine = create_async_engine(URL_DATABASE, echo=False, future=True)
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    yield async_session


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


#def pytest_collection_modifyitems(items):
#    pytest_asyncio_tests = (item for item in items if is_async_test(item))
#    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
#    for async_test in pytest_asyncio_tests:
#        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session", autouse=True)
async def run_migration():
    async with test_engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(base.metadata.drop_all)


@pytest.fixture(scope="session")
async def client(async_session_test_fixture) -> Generator[TestClient,  Any, None]:
    async def get_session_in_fixture() -> AsyncSession:
        async with async_session_test_fixture() as session:
            try:
                yield session
            finally:
                await session.close()
    app.dependency_overrides[get_session] = get_session_in_fixture
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
async def create_start_models(run_migration):
    async def create_state_accident():
        async with async_session_test() as session:
            response = select(func.count(StateAccident.id))
            result = await session.execute(response)
            count = result.scalars().first()
            if count == 0:
                clas = StateAccident(
                    name="empty",
                    description="Пустой"
                )
                class_meh = StateAccident(
                    name="pending",
                    description="На рассмотрении"
                )
                class_organizational = StateAccident(
                    name="accepted",
                    description="Принят"
                )

                session.add(class_organizational)
                session.add(class_meh)
                session.add(clas)
                await session.commit()
    async def create_prof():
        async with async_session_test() as session:
            try:
                response = select(func.count(Profession.id))
                result = await session.execute(response)
                count = result.scalars().first()
                if count == 0:
                    prof = Profession(
                        name="unknown",
                        description="Неизвестно"
                    )

                    session.add(prof)
                    await session.commit()
            finally:
                await session.close()
    async def create_user_contest():
        async with async_session_test() as session:
            try:
                response = select(func.count(User.id))
                result = await session.execute(response)
                count = result.scalars().first()
                if count == 0:
                    super_admin_type = TypeUser(
                        name="super_admin",
                        description=""
                    )
                    admin_type = TypeUser(
                        name="admin",
                        description=""
                    )
                    user_type = TypeUser(
                        name="user",
                        description=""
                    )
                    session.add(admin_type)
                    session.add(super_admin_type)
                    session.add(user_type)
                    await session.commit()
                    admin_user = User(
                        email="super_admin@super_admin.com",
                        id_type=super_admin_type.id
                    )
                    admin_user.password = "admin"
                    session.add(admin_user)

                    admin_user = User(
                        email="admin@admin.com",
                        id_type=admin_type.id
                    )
                    admin_user.password = "admin"
                    session.add(admin_user)

                    user_user = User(
                        email="user@user.com",
                        id_type=user_type.id,
                        name="user",
                        surname="user",
                        patronymic="user",
                    )
                    user_user.password = "user"
                    session.add(user_user)
                    await session.commit()
            finally:
                await session.close()
    async def create_object_context():
        async with async_session_test() as session:
            try:
                response = select(func.count(StateObject.id))
                result = await session.execute(response)
                count = result.scalars().first()
                if count == 0:
                    active_state = StateObject(
                        name="active",
                        description="активен"
                    )
                    inactive_type = StateObject(
                        name="inactive",
                        description="неактивен"
                    )

                    session.add(active_state)
                    session.add(inactive_type)
                    await session.commit()
            finally:
                await session.close()
    async def create_class_brake_context():
        async with async_session_test() as session:
            try:
                response = select(func.count(ClassBrake.id))
                result = await session.execute(response)
                count = result.scalars().first()
                if count == 0:
                    class_meh = ClassBrake(
                        name="meh",
                        description="механические"
                    )
                    class_organizational = ClassBrake(
                        name="external_organizational",
                        description="Внешние организационные"
                    )
                    class_organizational_1 = ClassBrake(
                        name="domestic_organizational",
                        description="Внутренние организационные"
                    )

                    session.add(class_organizational)
                    session.add(class_meh)
                    session.add(class_organizational_1)
                    await session.commit()
            finally:
                await session.close()
    async def create_event_context():
        async with async_session_test() as session:
            try:
                response = select(func.count(StateEvent.id))
                result = await session.execute(response)
                count = result.scalars().first()
                if count == 0:
                    done_state = StateEvent(
                        name="done",
                        description="Выполнено"
                    )
                    not_done_state = StateEvent(
                        name="not_done",
                        description="Не выполнено"
                    )

                    local_type_event = TypeEvent(
                        name="local",
                        description="Локальное"
                    )

                    general_type_event = TypeEvent(
                        name="general",
                        description="Общие"
                    )

                    session.add(done_state)
                    session.add(not_done_state)
                    session.add(local_type_event)
                    session.add(general_type_event)
                    await session.commit()
            finally:
                await session.close()
    async def create_state_claim_context():
        async with async_session_test() as session:
            try:
                response = select(func.count(StateClaim.id))
                result = await session.execute(response)
                count = result.scalars().first()
                if count == 0:
                    one = StateClaim(
                        name="under_consideration",
                        description="На рассмотрении"
                    )
                    two = StateClaim(
                        name="under_development",
                        description="На доработку"
                    )

                    threa = StateClaim(
                        name="accepted",
                        description="Принято"
                    )
                    ttt = StateClaim(
                        name="draft",
                        description="Черновик"
                    )

                    session.add(one)
                    session.add(two)
                    session.add(threa)
                    session.add(ttt)
                    await session.commit()
            finally:
                await session.close()

    await create_user_contest()
    await create_object_context()
    await create_class_brake_context()
    await create_event_context()
    await create_prof()
    await create_state_accident()
    await create_state_claim_context()
    return


#@pytest.fixture(scope="function")
#def get_user_token(client):
#    username = "admin@admin.com"
#    password = "admin"
#
#    response = client.post("/v1/login/sign-in", data={
#        "grant_type": "",
#        "username": username,
#        "password": password,
#        "client_id": "",
#        "client_secret": ""
#    },
#    headers={
#        'Content-Type': 'application/x-www-form-urlencoded',
#        'accept': 'application/json'
#    })
#    return response.json()["access_token"]