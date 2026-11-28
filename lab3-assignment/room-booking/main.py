import asyncio
import os
from datetime import date
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, model_validator

BOOKING_DELAY = float(os.getenv("BOOKING_DELAY", "0.0"))

app = FastAPI(title="Campus Room Booking Service")


class Room(BaseModel):
    id: str = Field(..., min_length=1)
    building: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0)


class BookingCreate(BaseModel):
    room_id: str = Field(..., min_length=1)
    date: date
    start_hour: int = Field(..., ge=8, le=20)
    end_hour: int = Field(..., ge=8, le=20)
    purpose: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def check_hours(self):
        if self.end_hour <= self.start_hour:
            raise ValueError("end_hour must be greater than start_hour")
        return self


class Booking(BookingCreate):
    booking_id: str


rooms: Dict[str, Room] = {}
bookings: Dict[str, Booking] = {}


def is_overlapping(b1: BookingCreate, b2: BookingCreate) -> bool:
    if b1.room_id != b2.room_id or b1.date != b2.date:
        return False
    return b1.start_hour < b2.end_hour and b2.start_hour < b1.end_hour


async def apply_delay() -> None:
    if BOOKING_DELAY > 0:
        await asyncio.sleep(BOOKING_DELAY)


@app.post("/rooms", status_code=status.HTTP_201_CREATED, response_model=Room)
async def add_room(room: Room):
    await apply_delay()
    if room.id in rooms:
        raise HTTPException(status_code=409, detail="Room already exists")
    rooms[room.id] = room
    return room


@app.get("/rooms", response_model=List[Room])
async def get_rooms():
    await apply_delay()
    return list(rooms.values())


@app.get("/rooms/{room_id}", response_model=Room)
async def get_room(room_id: str):
    await apply_delay()
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    return rooms[room_id]


@app.put("/bookings/{booking_id}", response_model=Booking)
async def book_room(booking_id: str, payload: BookingCreate, response: Response):
    await apply_delay()

    if payload.room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")

    if booking_id in bookings:
        existing = bookings[booking_id]
        if existing == Booking(booking_id=booking_id, **payload.model_dump()):
            return existing
        raise HTTPException(
            status_code=409,
            detail="Booking ID already used with different details",
        )

    for existing in bookings.values():
        if is_overlapping(payload, existing):
            raise HTTPException(
                status_code=409,
                detail="Booking overlaps with an existing booking",
            )

    new_booking = Booking(booking_id=booking_id, **payload.model_dump())
    bookings[booking_id] = new_booking
    response.status_code = status.HTTP_201_CREATED
    return new_booking


@app.get("/bookings", response_model=List[Booking])
async def get_bookings_by_date(
    room_id: str = Query(..., min_length=1),
    date: date = Query(...),
):
    await apply_delay()
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    return [
        booking
        for booking in bookings.values()
        if booking.room_id == room_id and booking.date == date
    ]


@app.get("/bookings/{booking_id}", response_model=Booking)
async def get_booking(booking_id: str):
    await apply_delay()
    if booking_id not in bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return bookings[booking_id]


@app.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str):
    await apply_delay()
    if booking_id not in bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    deleted = bookings.pop(booking_id)
    return {"deleted": deleted}