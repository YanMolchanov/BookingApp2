from fastapi import FastAPI, Depends, Path, HTTPException, status

from pandas import DataFrame as df
from datetime import timedelta
from typing import Annotated

import sqlalchemy as sa
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models import *

myapp = FastAPI()


@myapp.get("/")
async def read_main():
    return {"msg": "Hello World"}


# GET /tables/ — список всех столиков
@myapp.get("/tables", response_model=list[TablePublic], status_code=status.HTTP_200_OK)
async def get_tables(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Table))
    db_tables = result.scalars().all()
    if not db_tables:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Список столиков пуст")
    return [Table(name=t.name, seats=t.seats, location=t.location, id=t.id) for t in db_tables]


# POST /tables/ — создать новый столик
@myapp.post("/tables", response_model=TablePublic, status_code=status.HTTP_201_CREATED)
async def add_table(table: TableCreate, session: AsyncSession = Depends(get_session)):
    db_table = Table(name=table.name, seats=table.seats, location=table.location)
    session.add(db_table)
    await session.commit()
    await session.refresh(db_table)
    return db_table


# DELETE /tables/{id} — удалить столик
@myapp.delete("/tables/{id}", status_code=status.HTTP_200_OK)
async def delete_table(id: Annotated[int, Path(title="ID нужного стола", ge=1)],
                       session: AsyncSession = Depends(get_session)):
    db_table = await session.get(Table, id)
    if not db_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Столик с id {id} не найден")
    await session.delete(db_table)
    await session.commit()
    return {"ok": True}


# GET /reservations/ — список всех броней
@myapp.get("/reservations", response_model=list[ReservationPublic], status_code=status.HTTP_200_OK)
async def get_reservations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Reservation))
    db_reservations = result.scalars().all()
    if not db_reservations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Список бронирований пуст')
    return [Reservation(id=r.id,
                        customer_name=r.customer_name,
                        table_id=r.table_id,
                        reservation_time=r.reservation_time,
                        duration_minutes=r.duration_minutes)
            for r in db_reservations]


# POST /reservations/ — создать новую бронь
@myapp.post("/reservations", response_model=ReservationPublic, status_code=status.HTTP_201_CREATED)
async def add_reservation(reservation: ReservationCreate, session: AsyncSession = Depends(get_session)):
    db_table = await session.get(Table, reservation.table_id)
    if not db_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Столик с id {reservation.table_id} не найден")
    QUERY = f'''
               SELECT 
                   reservation_time, 
                   reservation_time + (INTERVAL \'1 min\' * duration_minutes) 
               FROM 
                   reservation
               WHERE
                   table_id = {reservation.table_id}
            '''
    result = await session.execute(sa.text(QUERY))
    result = result.fetchall()
    result.append([reservation.reservation_time,
                   reservation.reservation_time + timedelta(minutes=reservation.duration_minutes)])
    result = df(result, columns=["from", "to"])
    result = result.sort_values(by="from")
    result["overlap"] = (result["to"].shift()-result["from"]) > timedelta(0, 0, 0, 0)
    if (result["overlap"]).any():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Столик с id {reservation.table_id} занят в заданный промежуток времени!')
    db_reservation = Reservation(
        customer_name=reservation.customer_name,
        table_id=reservation.table_id,
        reservation_time=reservation.reservation_time,
        duration_minutes=reservation.duration_minutes)
    session.add(db_reservation)
    await session.commit()
    await session.refresh(db_reservation)
    return db_reservation


# DELETE /reservations/{id} — удалить бронь
@myapp.delete("/reservations/{id}", status_code=status.HTTP_200_OK)
async def delete_reservation(id: Annotated[int, Path(title="ID нужной брони", ge=1)],
                       session: AsyncSession = Depends(get_session)):
    db_reservation = await session.get(Reservation, id)
    if not db_reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Бронь с id {id} не найден')
    await session.delete(db_reservation)
    await session.commit()
    return {"ok": True}