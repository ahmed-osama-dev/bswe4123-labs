
from typing import Dict, List
from datetime import date

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, model_validator


app = FastAPI(title="Campus Room Booking Service")
# Pydantic Models
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
            raise ValueError(
                "end_hour must be greater than start_hour"
            )
        return self


class Booking(BookingCreate):
    booking_id: str

# In-memory Storage

rooms: Dict[str, Room] = {}
bookings: Dict[str, Booking] = {}
# Helper Function

def is_overlapping(b1: BookingCreate, b2: BookingCreate) -> bool:
    if b1.room_id != b2.room_id or b1.date != b2.date:
        return False

    return (
        b1.start_hour < b2.end_hour
        and b2.start_hour < b1.end_hour
    )

# Room Endpoints

@app.post(
    "/rooms",
    status_code=status.HTTP_201_CREATED,
    response_model=Room
)
def add_room(room: Room):

    if room.id in rooms:
        raise HTTPException(
            status_code=409,
            detail="Room already exists"
        )

    rooms[room.id] = room

    return room


@app.get("/rooms", response_model=List[Room])
def get_rooms():

    return list(rooms.values())


@app.get("/rooms/{room_id}", response_model=Room)
def get_room(room_id: str):

    if room_id not in rooms:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    return rooms[room_id]
# Booking Endpoints
@app.put(
    "/bookings/{booking_id}",
    response_model=Booking
)
def book_room(
    booking_id: str,
    payload: BookingCreate,
    response: Response
):
    # Check if room exists
    if payload.room_id not in rooms:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    # Check Idempotency
    if booking_id in bookings:

        existing = bookings[booking_id]

        if existing == Booking(
            booking_id=booking_id,
            **payload.model_dump()
        ):
            return existing

        raise HTTPException(
            status_code=409,
            detail="Booking ID already used with different details"
        )
    # Check overlapping bookings
    for existing in bookings.values():

        if is_overlapping(payload, existing):
            raise HTTPException(
                status_code=409,
                detail="Booking overlaps with an existing booking"
            )
    # Create new booking
    new_booking = Booking(
        booking_id=booking_id,
        **payload.model_dump()
    )

    bookings[booking_id] = new_booking

    response.status_code = status.HTTP_201_CREATED

    return new_booking
@app.get("/bookings", response_model=List[Booking])
def get_bookings_by_date(
    room_id: str = Query(..., min_length=1),
    date: date = Query(...)
):

    if room_id not in rooms:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    return [
        booking
        for booking in bookings.values()
        if booking.room_id == room_id
        and booking.date == date
    ]
@app.get("/bookings/{booking_id}", response_model=Booking)
def get_booking(booking_id: str):

    if booking_id not in bookings:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )
    return bookings[booking_id]
@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str):
    if booking_id not in bookings:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )
    deleted = bookings.pop(booking_id)
    return {
        "deleted": deleted
    }
