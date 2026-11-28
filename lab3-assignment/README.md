# Lab 3 - Exam Scheduler Service

## 1. Project Overview

In this lab, I built an Exam Scheduler Service using Python and FastAPI. The system is used to schedule university exams and select a suitable room based on the number of students and the available time.

The project contains two services:

- **Exam Scheduler Service:** Receives exam requests, checks available rooms, and schedules exams.
- **Room Booking Service:** Manages rooms and bookings and checks for time conflicts.

The two services communicate using HTTP requests.

## 2. Project Structure

```text
lab3-assignment/
│
├── exam-scheduler/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env
│
├── room-booking/
│   ├── main.py
│   ├── requirements.txt
│   └── .env
│
└── README.md
```

## 3. Technologies Used

- Python
- FastAPI
- Uvicorn
- HTTPX
- Pydantic
- python-dotenv

## 4. Installation

First, open PowerShell and go to the project folder:

```powershell
cd lab3-assignment
```

Install the dependencies for the Room Booking Service:

```powershell
cd room-booking
python -m pip install -r requirements.txt
```

Then install the dependencies for the Exam Scheduler Service:

```powershell
cd ..\exam-scheduler
python -m pip install -r requirements.txt
```

## 5. Environment Configuration

### Room Booking Service

The `.env` file contains:

```env
BOOKING_DELAY=0
```

This value means that there is no artificial delay by default.

### Exam Scheduler Service

The `config.py` file reads the following environment variables:

| Variable | Default Value | Description |
|---|---|---|
| ROOM_BOOKING_URL | http://127.0.0.1:8001 | Room Booking Service URL |
| REQUEST_TIMEOUT | 2.0 | Request timeout in seconds |
| MAX_RETRIES | 3 | Maximum number of retries |

The `.env` file for this service is currently empty, so the default values are used unless environment variables are set manually.

## 6. Running the Services

The two services must run separately in two PowerShell terminals.

### Terminal 1: Room Booking Service

```powershell
cd lab3-assignment\room-booking
python -m uvicorn main:app --reload --port 8001 --env-file .env
```

The service runs at:

http://127.0.0.1:8001

### Terminal 2: Exam Scheduler Service

```powershell
cd lab3-assignment\exam-scheduler
python -m uvicorn main:app --reload --port 8002
```

The service runs at:

http://127.0.0.1:8002

The API documentation is available at:

- Room Booking: http://127.0.0.1:8001/docs
- Exam Scheduler: http://127.0.0.1:8002/docs

## 7. Main API Endpoints

### Room Booking Service

| Method | Endpoint | Description |
|---|---|---|
| POST | `/rooms` | Add a new room |
| GET | `/rooms` | Get all rooms |
| GET | `/rooms/{room_id}` | Get a specific room |
| PUT | `/bookings/{booking_id}` | Create a room booking |
| GET | `/bookings` | Get bookings by room and date |
| GET | `/bookings/{booking_id}` | Get a specific booking |
| DELETE | `/bookings/{booking_id}` | Delete a booking |

### Exam Scheduler Service

| Method | Endpoint | Description |
|---|---|---|
| POST | `/exams` | Schedule a new exam |
| GET | `/config` | Get the current configuration |

## 8. How Exam Scheduling Works

When the Exam Scheduler receives a new exam request, it performs the following steps:

1. Gets all rooms from the Room Booking Service.
2. Filters rooms that have enough capacity for the students.
3. Sorts the suitable rooms from smallest to largest.
4. Checks the bookings of each room on the requested date.
5. Checks if the requested time is available.
6. Sends a booking request to the Room Booking Service.
7. Returns the exam information and the selected room.

If no suitable room is available, the service returns `409 Conflict`.

If the Room Booking Service is unreachable, the service returns `503 Service Unavailable`.

## 9. Retry Mechanism

I implemented a retry mechanism using HTTPX and `asyncio`.

The system retries requests when it receives:

- Timeout errors.
- Connection errors.
- Server errors (5xx).

It does not retry client errors (4xx), such as `404` and `409`.

The retry mechanism uses Exponential Backoff:

| Retry | Waiting Time |
|---|---|
| First retry | 0.5 seconds |
| Second retry | 1 second |
| Third retry | 2 seconds |

The waiting time increases after each failed attempt.

### Why is the booking request safe to retry?

The booking request uses the HTTP PUT method with a fixed booking ID:

```python
booking_id = f"exam-{exam.id}"
```

The Room Booking Service checks whether this booking ID already exists. If the same request is sent again with the same data, it returns the existing booking instead of creating a duplicate.

This makes retrying the same booking request safe in the current implementation.

## 10. Retry Testing

I tested the retry mechanism by stopping the Room Booking Service while sending an exam request.

The Exam Scheduler tried to connect several times and waited between attempts.

The log showed the following retry delays:

```text
0.5 seconds
1.0 seconds
2.0 seconds
```

After the retries were exhausted, the Exam Scheduler returned:

```text
503 Service Unavailable
```

I also restarted the Room Booking Service and tested exam scheduling again. The service was able to communicate with it and complete a booking successfully.

## 11. Artificial Delay Testing

I added an artificial delay to the Room Booking Service using the `BOOKING_DELAY` environment variable.

For testing, I used:

```powershell
$env:BOOKING_DELAY="3.0"
```

This adds a 3-second delay to each request.

I tested different timeout values in the Exam Scheduler.

### Test 1: Short Timeout

```powershell
$env:REQUEST_TIMEOUT="1.0"
$env:MAX_RETRIES="2"
python -m uvicorn main:app --reload --port 8002
```

The Room Booking Service had a 3-second delay, while the request timeout was only 1 second.

The requests timed out, and the Exam Scheduler returned `503 Service Unavailable` after the retries.

### Test 2: Longer Timeout

```powershell
$env:REQUEST_TIMEOUT="4.0"
$env:MAX_RETRIES="2"
python -m uvicorn main:app --reload --port 8002
```

The timeout was increased to 4 seconds.

The requests succeeded because the timeout was longer than the artificial delay.

### Test Results

| Test | Booking Delay | Timeout | Max Retries | Result |
|---|---:|---:|---:|---|
| Short timeout | 3 sec | 1 sec | 2 | 503 Service Unavailable |
| Longer timeout | 3 sec | 4 sec | 2 | 201 Created |

During the successful test, the total execution time was approximately 9.3 seconds because the Exam Scheduler made three sequential requests to the Room Booking Service, and each request took about 3 seconds.

### Explanation

When the timeout is shorter than the service delay, requests fail even if the service is running.

When the timeout is longer than the service delay, requests have enough time to complete successfully.

However, increasing the timeout can make the user wait longer for a response. Therefore, choosing the timeout value depends on the expected response time of the other service.

## 12. Important Notes

- Both services currently store rooms and bookings in memory using Python dictionaries.
- Data is lost when the Room Booking Service restarts.
- Both services must be running for exam scheduling to work.
- The default artificial delay is zero.
- Environment variables can be changed to test different configurations.

## 13. Conclusion

In this lab, I learned how to build two separate FastAPI services and make them communicate using HTTP requests.

I also learned how to use environment variables, implement retry logic with Exponential Backoff, handle service failures, and test the effect of artificial delays and request timeouts.

The project helped me understand how multiple services can work together and how to handle communication problems between them.