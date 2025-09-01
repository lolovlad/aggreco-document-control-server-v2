from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
    Float,
    Date
)

from sqlalchemy.dialects.postgresql import JSONB, UUID
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash


base = declarative_base()


class DeleteMixin(object):
    is_delite = Column(Boolean, default=False, nullable=True, server_default="False")


class TypeUser(base):
    __tablename__ = "type_user"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(32), nullable=False, unique=True)
    description = Column(String(128), nullable=True)


class Profession(base):
    __tablename__ = "profession"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(128), nullable=True)


class User(base):
    __tablename__ = "user"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)

    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    patronymic = Column(String, nullable=True)

    email = Column(String, nullable=True, unique=True)
    password_hash = Column(String, nullable=True)
    id_type = Column(Integer, ForeignKey("type_user.id"))
    id_profession = Column(Integer, ForeignKey("profession.id"))
    type = relationship("TypeUser", lazy="joined")
    profession = relationship("Profession", lazy="joined")

    painting = Column(String, nullable=True, default="")
    email_send_info = Column(MutableDict.as_mutable(JSONB), nullable=True)

    is_deleted = Column(Boolean, nullable=True, default=False)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, val: str):
        self.password_hash = generate_password_hash(val)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Document(base):
    __tablename__ = "document"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)
    name = Column(String(32), unique=True, nullable=False)
    url_document = Column(String, nullable=False)
    data_create = Column(DateTime, nullable=False, default=datetime.now())
    description = Column(Text, nullable=True)

    users_document = relationship("UserToDocument", lazy="joined")


class UserToDocument(base):
    __tablename__ = "user_to_document"
    id_document = Column(ForeignKey("document.id"), primary_key=True)
    id_user = Column(ForeignKey("user.id"), primary_key=True)
    user = relationship("User", lazy="joined")
    datetime_view = Column(DateTime, default=datetime.now())


class StateObject(base):
    __tablename__ = "state_object"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(128), nullable=True)


class TypeEquipment(base):
    __tablename__ = "type_equipment"
    id = Column(Integer, autoincrement=True, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(128), nullable=True)


class Region(base):
    __tablename__ = "region"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(128), nullable=False, unique=True)


class Object(base):
    __tablename__ = "object"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)
    name = Column(String(256), nullable=False)
    address = Column(String(256), nullable=False)

    id_region = Column(ForeignKey("region.id"), nullable=True)
    region = relationship("Region", lazy="joined")

    cx = Column(Float, nullable=True, default=0.0)
    cy = Column(Float, nullable=True, default=0.0)
    description = Column(Text, nullable=True)
    counterparty = Column(String(256), nullable=False)
    id_state = Column(ForeignKey("state_object.id"))
    state = relationship("StateObject", lazy="joined")
    equipment = relationship("Equipment", cascade="all, delete")
    staff = relationship(User, secondary="object_to_user")

    is_deleted = Column(Boolean, nullable=True, default=False)


class Equipment(base):
    __tablename__ = "equipment"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)
    id_object = Column(ForeignKey("object.id"))
    name = Column(String(256), nullable=False)
    code = Column(String, nullable=True)
    id_type = Column(ForeignKey("type_equipment.id"))
    type = relationship("TypeEquipment", lazy="joined")
    description = Column(Text, nullable=True)
    characteristics = Column(JSONB, nullable=True)

    is_delite = Column(Boolean, default=False, nullable=True, server_default="False")


class ObjectToUser(base):
    __tablename__ = "object_to_user"
    id_object = Column(ForeignKey("object.id"), primary_key=True)
    id_user = Column(ForeignKey("user.id"), primary_key=True)


class ClassBrake(base):
    __tablename__ = "class_brake"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String, unique=True, nullable=False, default="1.1")
    description = Column(String, nullable=True)


class TypeBrake(base):
    __tablename__ = "type_brake"
    id = Column(Integer, autoincrement=True, primary_key=True)
    code = Column(String, unique=True, nullable=False, default="1.1")
    name = Column(String, nullable=False)
    id_type = Column(ForeignKey("class_brake.id"))
    type = relationship(ClassBrake, lazy="joined")


class SignsAccident(base):
    __tablename__ = "signs_accident"
    id = Column(Integer, autoincrement=True, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)


class StateEvent(base):
    __tablename__ = "state_event"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String, unique=True, nullable=False, default="")
    description = Column(String, nullable=True)


class TypeEvent(base):
    __tablename__ = "type_event"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String, unique=True, nullable=False, default="")
    description = Column(String, nullable=True)


class Event(base):
    __tablename__ = "event"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)
    description = Column(Text, nullable=False)
    date_finish = Column(Date, nullable=False)

    id_accident = Column(ForeignKey("accident.id"))
    accident = relationship("Accident", lazy="joined")

    id_state_event = Column(ForeignKey("state_event.id"))
    state_event = relationship(StateEvent, lazy="joined")

    id_type_event = Column(ForeignKey("type_event.id"))
    type_event = relationship(TypeEvent, lazy="joined")
    responsible = Column(String, nullable=True)


class StateAccident(base):
    __tablename__ = "state_accident"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(32), nullable=False, unique=True)
    description = Column(String(128), nullable=True)


class Accident(DeleteMixin, base):
    __tablename__ = "accident"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)

    id_object = Column(ForeignKey("object.id"))
    object = relationship(Object, lazy="joined")

    signs_accident = relationship(SignsAccident, secondary="signs_accident_to_accident", lazy="joined")

    damaged_equipment = relationship(Equipment, secondary="equipment_to_accident", lazy="joined")

    datetime_start = Column(DateTime(timezone=False), nullable=False)
    datetime_end = Column(DateTime(timezone=False), nullable=True)

    type_brakes = relationship(TypeBrake, secondary="type_brake_to_accident", lazy="joined")

    time_line = Column(MutableDict.as_mutable(JSONB), nullable=False)

    causes_of_the_emergency = Column(Text, nullable=False)
    damaged_equipment_material = Column(Text, nullable=False)

    event = relationship(Event, back_populates="accident", lazy="joined")

    additional_material = Column(String, nullable=True, default="")

    id_state_accident = Column(ForeignKey("state_accident.id"))
    state_accident = relationship(StateAccident, lazy="joined")

    time_zone = Column(String, nullable=True, default="+03:00", server_default="+03:00")


class SignsAccidentToAccident(base):
    __tablename__ = "signs_accident_to_accident"
    id_accident = Column(ForeignKey("accident.id"), primary_key=True)
    id_signs_accident = Column(ForeignKey("signs_accident.id"), primary_key=True)


class TypeBrakeToAccident(base):
    __tablename__ = "type_brake_to_accident"
    id_accident = Column(ForeignKey("accident.id"), primary_key=True)
    id_type_brake = Column(ForeignKey("type_brake.id"), primary_key=True)


class EquipmentToAccident(base):
    __tablename__ = "equipment_to_accident"
    id_accident = Column(ForeignKey("accident.id"), primary_key=True)
    id_equipment = Column(ForeignKey("equipment.id"), primary_key=True)


class StateClaim(base):
    __tablename__ = "state_claim"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(32), nullable=False, unique=True)
    description = Column(String(128), nullable=True)


class Claim(base):
    __tablename__ = "claim"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)

    datetime = Column(DateTime(timezone=True), nullable=False)

    id_state_claim = Column(ForeignKey("state_claim.id"))
    state_claim = relationship(StateClaim, lazy="joined")

    id_user = Column(ForeignKey("user.id"))
    user = relationship(User, lazy="joined")

    main_document = Column(String, nullable=True)

    edit_document = Column(String, nullable=True)
    comment = Column(Text, nullable=True, default="Нет")
    id_accident = Column(ForeignKey("accident.id"))
    accident = relationship(Accident, lazy="joined", cascade="all, delete")

    last_datetime_edit = Column(DateTime(timezone=True),
                                nullable=False,
                                onupdate=func.now(),
                                server_default=func.now())


class FileDocument(base):
    __tablename__ = "file_document"
    id = Column(Integer, autoincrement=True, primary_key=True)

    file_key = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    datetime = Column(DateTime(timezone=True), nullable=False, default=datetime.now)

    name = Column(String, nullable=True)
    size = Column(Float, nullable=True)
