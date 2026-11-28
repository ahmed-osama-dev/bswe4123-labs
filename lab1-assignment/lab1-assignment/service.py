
import os
import time
import uvicorn
from fastapi import FastAPI

app = FastAPI()
START_TIME = time.time()
DELAY_SECONDS = float(os.getenv("DELAY_SECONDS", "0"))


@app.get("/health")
def health():
    if DELAY_SECONDS > 0:
        time.sleep(DELAY_SECONDS)
    uptime_seconds = round(time.time() - START_TIME, 2)
    return {
        "status": "ok",
        "uptime_seconds": uptime_seconds,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="127.0.0.1", port=port)
