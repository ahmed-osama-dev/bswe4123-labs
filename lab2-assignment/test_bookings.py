
import httpx

BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Rooms Tests
        res = client.post(
            "/rooms",
            json={
                "id": "B205",
                "building": "B",
                "capacity": 30,
            },
        )
        print("POST /rooms (create):", res.status_code)

        res = client.post(
            "/rooms",
            json={
                "id": "B205",
                "building": "B",
                "capacity": 30,
            },
        )
        print("POST /rooms (duplicate):", res.status_code)

        res = client.get("/rooms")
        print(
            "GET /rooms:",
            res.status_code,
            "count =",
            len(res.json()),
        )

        res = client.get("/rooms/B205")
        print("GET /rooms/B205:", res.status_code)

        res = client.get("/rooms/NO_SUCH_ROOM")
        print("GET /rooms/NO_SUCH_ROOM:", res.status_code)
        # 2. Validation Tests
        res = client.put(
            "/bookings/bk-invalid-hours",
            json={
                "room_id": "B205",
                "date": "2026-11-25",
                "start_hour": 14,
                "end_hour": 12,
                "purpose": "Invalid range",
            },
        )
        print("Invalid hours:", res.status_code)

        res = client.put(
            "/bookings/bk-outside-hours",
            json={
                "room_id": "B205",
                "date": "2026-11-25",
                "start_hour": 7,
                "end_hour": 9,
                "purpose": "Before 8:00",
            },
        )
        print("Outside allowed hours:", res.status_code)

        res = client.put(
            "/bookings/bk-invalid-date",
            json={
                "room_id": "B205",
                "date": "2026-99-99",
                "start_hour": 10,
                "end_hour": 12,
                "purpose": "Invalid date",
            },
        )
        print("Invalid date:", res.status_code)

        res = client.put(
            "/bookings/bk-missing-room",
            json={
                "room_id": "UNKNOWN",
                "date": "2026-11-25",
                "start_hour": 9,
                "end_hour": 11,
                "purpose": "Room does not exist",
            },
        )
        print("Missing room:", res.status_code)
        # 3. Booking Creation
        booking_payload = {
            "room_id": "B205",
            "date": "2026-11-25",
            "start_hour": 10,
            "end_hour": 12,
            "purpose": "Study group",
        }

        res = client.put(
            "/bookings/bk-1",
            json=booking_payload,
        )
        print("Create booking:", res.status_code)
        # 4. Idempotency Test
        res_retry = client.put(
            "/bookings/bk-1",
            json=booking_payload,
        )
        print("Retry same booking:", res_retry.status_code)

        res = client.get(
            "/bookings",
            params={
                "room_id": "B205",
                "date": "2026-11-25",
            },
        )

        print(
            "Bookings after retry:",
            res.status_code,
            "count =",
            len(res.json()),
        )
        # 5. Overlap Tests
        res = client.put(
            "/bookings/bk-2",
            json={
                "room_id": "B205",
                "date": "2026-11-25",
                "start_hour": 11,
                "end_hour": 13,
                "purpose": "Overlapping meeting",
            },
        )
        print("Overlapping booking:", res.status_code)

        res = client.put(
            "/bookings/bk-3",
            json={
                "room_id": "B205",
                "date": "2026-11-25",
                "start_hour": 12,
                "end_hour": 13,
                "purpose": "Adjacent lab session",
            },
        )
        print("Adjacent booking:", res.status_code)
        # 6. Get Booking Tests
        res = client.get("/bookings/bk-1")
        print("GET /bookings/bk-1:", res.status_code)

        res = client.get("/bookings/UNKNOWN")
        print("GET unknown booking:", res.status_code)
        # 7. Delete Booking Tests
        res = client.delete("/bookings/bk-1")
        print("DELETE /bookings/bk-1:", res.status_code)

        res = client.get("/bookings/bk-1")
        print("GET booking after delete:", res.status_code)

        res = client.delete("/bookings/bk-1")
        print("DELETE booking again:", res.status_code)


if __name__ == "__main__":
    main()
