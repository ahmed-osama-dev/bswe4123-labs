import os
from pydantic import BaseModel


class SchedulerConfig(BaseModel):
    room_booking_url: str
    request_timeout: float
    max_retries: int


def load_config() -> SchedulerConfig:
    return SchedulerConfig(
        room_booking_url=os.getenv("ROOM_BOOKING_URL", "http://127.0.0.1:8001").rstrip("/"),
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "2.0")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
    )