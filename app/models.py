from sqlmodel import Field, SQLModel
from pydantic import field_validator
import datetime as dt


class TableBase(SQLModel):
    name: str | None = Field(default=None, title="Наименование столика")
    seats: int = Field(title="Количество мест", gt=0)
    location: str | None = Field(default=None, title="Место расположения")


class Table(TableBase, table=True):
    id: int | None = Field(default=None, title="id столика", primary_key=True)


class TablePublic(TableBase):
    id: int


class TableCreate(TableBase):
    pass


class TableUpdate(TableBase):
    name: str | None = None
    seats: int | None = None
    location: str | None = None


class ReservationBase(SQLModel):
    customer_name: str = Field(title="Имя посетителя")
    table_id: int = Field(title="id столика", foreign_key="table.id", gt=0)
    reservation_time: dt.datetime = Field(title="Дата и время брони")
    duration_minutes: int = Field(title="Продожительность брони (мин.)")

    @field_validator("reservation_time")
    @classmethod
    def remove_timezone(cls, reservation_time) -> dt.datetime:
        return reservation_time.replace(tzinfo=None)


class Reservation(ReservationBase, table=True):
    id: int | None = Field(default=None, title="id брони", primary_key=True)


class ReservationPublic(ReservationBase):
    id: int


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(ReservationBase):
    customer_name: str | None = None
    table_id: int | None = None
    reservation_time: dt.datetime | None = None
    duration_minutes: int | None = None

    @field_validator("reservation_time")
    @classmethod
    def remove_timezone(cls, reservation_time) -> dt.datetime:
        return reservation_time.replace(tzinfo=None)



