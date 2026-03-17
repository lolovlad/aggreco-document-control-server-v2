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


base = declarative_base()


class DeleteMixin(object):
    is_delite = Column(Boolean, default=False, nullable=True, server_default="False")


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
    user_uuid = Column(UUID(as_uuid=True), primary_key=True)
    datetime_view = Column(DateTime, default=datetime.now())


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


class CodeErrorAccident(base):
    __tablename__ = "code_error_accident"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)


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

    uuid_object = Column(UUID(as_uuid=True), nullable=True)

    signs_accident = relationship(SignsAccident, secondary="signs_accident_to_accident", lazy="joined")
    damaged_equipment = relationship("EquipmentToAccident", lazy="joined")

    datetime_start = Column(DateTime(timezone=False), nullable=False)
    datetime_end = Column(DateTime(timezone=False), nullable=True)

    type_brakes = relationship(TypeBrake, secondary="type_brake_to_accident", lazy="joined")
    id_error_code_accident = Column(ForeignKey(CodeErrorAccident.id))
    error_code_accident = relationship(CodeErrorAccident, lazy="joined")

    time_line = Column(MutableDict.as_mutable(JSONB), nullable=False)

    causes_of_the_emergency = Column(Text, nullable=False)
    reason_for_shutdown = Column(Text, nullable=True)
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
    uuid_equipment = Column(UUID(as_uuid=True), primary_key=True)


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

    user_uuid = Column(UUID(as_uuid=True))

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


class TechnicalProposals(base):
    __tablename__ = "technical_proposals"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)

    name = Column(String, nullable=True, default=None)

    id_state_claim = Column(ForeignKey("state_claim.id"))
    state_claim = relationship(StateClaim, lazy="joined")

    # UUID объекта из внешнего микросервиса
    uuid_object = Column(UUID(as_uuid=True))

    # UUID пользователя и эксперта вместо локальных id
    user_uuid = Column(UUID(as_uuid=True))
    expert_uuid = Column(UUID(as_uuid=True), nullable=True, default=None)

    offer = Column(Text, nullable=True)
    additional_material = Column(String, nullable=True, default="")

    comment = Column(Text, nullable=True, default="Нет")

    last_datetime_edit = Column(DateTime(timezone=True),
                                nullable=False,
                                onupdate=func.now(),
                                server_default=func.now())


class LogMessageError(base):
    __tablename__ = "log_messages_error"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)

    # UUID объекта и оборудования из внешнего микросервиса
    uuid_object = Column(UUID(as_uuid=True), nullable=True)
    uuid_equipment = Column(UUID(as_uuid=True), nullable=True)

    create_at = Column(DateTime(timezone=False), nullable=False)
    
    message = Column(Text, nullable=False)

    class_log_text = Column(String, nullable=False)
    class_log_int = Column(Integer, nullable=False)

    is_processed = Column(Boolean, default=False)

    entity_equipment = Column(String, nullable=True)
    number_equipment = Column(Integer, nullable=True)


class Summarize(base):
    __tablename__ = "summatize"
    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid4)

    # UUID объекта и оборудования из внешнего микросервиса
    uuid_object = Column(UUID(as_uuid=True), nullable=True)
    uuid_equipment = Column(UUID(as_uuid=True), nullable=True)
    text = Column(Text, nullable=False)

    datetime_start = Column(DateTime(timezone=False), nullable=False)
    datetime_end = Column(DateTime(timezone=False), nullable=True)

    metadata_equipment = Column(MutableDict.as_mutable(JSONB), nullable=False)

