
# Lab Assignment 2 - Campus Room Booking Service

## 1. API Design

| Action | Method | Endpoint | Success | Errors |
| :--- | :--- | :--- | :--- | :--- |
| Add Room | `POST` | `/rooms` | `201` | `409, 422` |
| Get All Rooms | `GET` | `/rooms` | `200` | None |
| Get Room by ID | `GET` | `/rooms/{room_id}` | `200` | `404` |
| Book a Room | `PUT` | `/bookings/{booking_id}` | `201 / 200` | `404, 409, 422` |
| Get Bookings by Date | `GET` | `/bookings?room_id=...&date=...` | `200` | `404, 422` |
| Get Booking by ID | `GET` | `/bookings/{booking_id}` | `200` | `404` |
| Delete Booking | `DELETE` | `/bookings/{booking_id}` | `200` | `404` |

## 2. Safe to Retry (Idempotency)

In this assignment, I used `PUT` with a `booking_id` to make sure that sending the same booking request more than once does not create duplicate bookings.

The booking works as follows:

- **First request:** If the booking ID is new and the data is valid, the booking is created and the server returns `201 Created`.
- **Same request again:** If I send the same booking ID with the same data, the server returns `200 OK` without creating another booking.
- **Same ID with different data:** The server returns `409 Conflict` because this booking ID is already used.

I tested this in `test_bookings.py` by sending the same request for `bk-1` twice. The first request returned `201`, and the second returned `200`. I also checked the bookings list and found that the count was still `1`.

## 3. Client Script Output (`test_bookings.py`)

I ran the test script using `python test_bookings.py`. The output below shows the results of the tests:

```text
POST /rooms (create): 201
POST /rooms (duplicate): 409
GET /rooms: 200 count = 1
GET /rooms/B205: 200
GET /rooms/NO_SUCH_ROOM: 404
Invalid hours: 422
Outside allowed hours: 422
Invalid date: 422
Missing room: 404
Create booking: 201
Retry same booking: 200
Bookings after retry: 200 count = 1
Overlapping booking: 409
Adjacent booking: 201
GET /bookings/bk-1: 200
GET unknown booking: 404
DELETE /bookings/bk-1: 200
GET booking after delete: 404
DELETE booking again: 404
```
