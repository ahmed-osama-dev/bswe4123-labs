
import asyncio
import logging
from datetime import date
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("exam-scheduler")

config = load_config()
app = FastAPI(title="Exam Scheduler Service")


class ExamRequest(BaseModel):
    id: str = Field(..., min_length=1)
    course_code: str = Field(..., min_length=1)
    day: date
    start_hour: int = Field(..., ge=8, le=20)
    end_hour: int = Field(..., ge=8, le=20)
    students_count: int = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_hours(self):
        if self.end_hour <= self.start_hour:
            raise ValueError("end_hour must be greater than start_hour")
        return self


class ExamScheduleResponse(BaseModel):
    exam_id: str
    course_code: str
    day: date
    start_hour: int
    end_hour: int
    students_count: int
    room: Dict[str, Any]
    booking: Dict[str, Any]


def is_time_free(
    bookings_list: List[Dict[str, Any]],
    start_hour: int,
    end_hour: int,
) -> bool:
    for b in bookings_list:
        if start_hour < b["end_hour"] and b["start_hour"] < end_hour:
            return False
    return True


async def request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> httpx.Response:

    url = f"{config.room_booking_url}{path}"
    attempt = 0

    while True:
        try:
            logger.info(
                "Sending %s %s (attempt %d/%d)",
                method,
                url,
                attempt + 1,
                config.max_retries + 1,
            )

            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                timeout=config.request_timeout,
            )

            # Never retry 4xx errors
            if 400 <= response.status_code < 500:
                logger.warning(
                    "Non-retriable status %d from %s",
                    response.status_code,
                    url,
                )
                return response

            # Retry on 5xx server errors
            if response.status_code >= 500:
                if attempt >= config.max_retries:
                    logger.error(
                        "Exhausted retries (%d) on %d from %s",
                        config.max_retries,
                        response.status_code,
                        url,
                    )
                    return response

                backoff = 0.5 * (2 ** attempt)

                logger.warning(
                    "Server error %d on %s; retrying in %.1fs...",
                    response.status_code,
                    url,
                    backoff,
                )

                await asyncio.sleep(backoff)
                attempt += 1
                continue

            return response

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            if attempt >= config.max_retries:
                logger.error(
                    "Failed after %d retries on %s: %s",
                    config.max_retries,
                    url,
                    type(exc).__name__,
                )
                raise

            backoff = 0.5 * (2 ** attempt)

            logger.warning(
                "%s on %s; retrying in %.1fs (attempt %d/%d)...",
                type(exc).__name__,
                url,
                backoff,
                attempt + 1,
                config.max_retries,
            )

            await asyncio.sleep(backoff)
            attempt += 1


@app.get("/config")
def get_config():
    return {
        "room_booking_url": config.room_booking_url,
        "request_timeout": config.request_timeout,
        "max_retries": config.max_retries,
    }


@app.post(
    "/exams",
    status_code=status.HTTP_201_CREATED,
    response_model=ExamScheduleResponse,
)
async def schedule_exam(exam: ExamRequest):

    async with httpx.AsyncClient() as client:

        # Get available rooms
        try:
            rooms_resp = await request_with_retry(
                client,
                "GET",
                "/rooms",
            )
        except (httpx.TimeoutException, httpx.ConnectError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Room Booking Service unreachable while fetching rooms",
            )

        if rooms_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unexpected response fetching rooms: {rooms_resp.status_code}",
            )

        rooms_data: List[Dict[str, Any]] = rooms_resp.json()

        # Select the smallest room that can fit all students
        candidate_rooms = sorted(
            [
                r for r in rooms_data
                if r["capacity"] >= exam.students_count
            ],
            key=lambda r: r["capacity"],
        )

        booking_id = f"exam-{exam.id}"

        for room in candidate_rooms:

            # Check existing bookings for this room and date
            try:
                bookings_resp = await request_with_retry(
                    client,
                    "GET",
                    "/bookings",
                    params={
                        "room_id": room["id"],
                        "date": exam.day.isoformat(),
                    },
                )
            except (httpx.TimeoutException, httpx.ConnectError):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Room Booking Service unreachable while checking availability",
                )

            if bookings_resp.status_code >= 500:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Room Booking Service unavailable while checking availability",
                )

            if bookings_resp.status_code == 404:
                continue

            if bookings_resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Unexpected response checking bookings: {bookings_resp.status_code}",
                )

            if not is_time_free(
                bookings_resp.json(),
                exam.start_hour,
                exam.end_hour,
            ):
                continue

            # Prepare booking request
            payload = {
                "room_id": room["id"],
                "date": exam.day.isoformat(),
                "start_hour": exam.start_hour,
                "end_hour": exam.end_hour,
                "purpose": f"Exam {exam.course_code} ({exam.id})",
            }

            try:
                book_resp = await request_with_retry(
                    client,
                    "PUT",
                    f"/bookings/{booking_id}",
                    json_body=payload,
                )
            except (httpx.TimeoutException, httpx.ConnectError):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Room Booking Service unreachable while booking room",
                )

            if book_resp.status_code in (200, 201):
                return ExamScheduleResponse(
                    exam_id=exam.id,
                    course_code=exam.course_code,
                    day=exam.day,
                    start_hour=exam.start_hour,
                    end_hour=exam.end_hour,
                    students_count=exam.students_count,
                    room=room,
                    booking=book_resp.json(),
                )

            if book_resp.status_code == 409:
                # Room was booked by another request; try the next room
                continue

            if book_resp.status_code >= 500:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Room Booking Service failed with 5xx during booking",
                )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unexpected booking response: {book_resp.status_code}",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No free room with sufficient capacity available for the requested time",
        )
