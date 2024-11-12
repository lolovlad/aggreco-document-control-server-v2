from sqlalchemy import select, func
from asyncio import run
from server.database import async_session
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
from uuid import uuid4


async def create_state_accident():
    async with async_session() as session:
        try:
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
        finally:
            await session.close()


async def create_prof():
    async with async_session() as session:
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
    async with async_session() as session:
        try:
            response = select(func.count(User.id))
            result = await session.execute(response)
            count = result.scalars().first()
            if count == 0:
                admin_type = TypeUser(
                    name="admin",
                    description=""
                )
                user_type = TypeUser(
                    name="user",
                    description=""
                )
                session.add(admin_type)
                session.add(user_type)
                await session.commit()
                admin_user = User(
                    email="lll-ooo-2003@mail.ru",
                    id_type=admin_type.id
                )
                admin_user.password = "admin"
                session.add(admin_user)
                await session.commit()
        finally:
            await session.close()


async def create_object_context():
    async with async_session() as session:
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
    async with async_session() as session:
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
                    name="org",
                    description="организационные"
                )

                session.add(class_organizational)
                session.add(class_meh)
                await session.commit()
        finally:
            await session.close()


async def create_event_context():
    async with async_session() as session:
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
    async with async_session() as session:
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


async def main():
    await create_user_contest()
    await create_object_context()
    await create_class_brake_context()
    await create_event_context()
    await create_prof()
    await create_state_accident()
    await create_state_claim_context()

run(main())