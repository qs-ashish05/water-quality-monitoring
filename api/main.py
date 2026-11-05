from zoneinfo import ZoneInfo
from datetime import datetime
from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import asyncio
import random


def get_generated_at():
    ist_time = datetime.now(ZoneInfo("Asia/Kolkata"))

    return {
        "Date": ist_time.strftime("%d-%m-%Y"),
        "Time": ist_time.strftime("%H:%M:%S")
    }

# Shared sensor readings
sensor_data = {}

def generate_readings():
   

    # 1. Temperature
    temperature = round(random.uniform(18, 34), 2)

    if 20 <= temperature <= 25:
        temp_tag = "In the desirable range"
        temp_safe = True
    else:
        temp_tag = "Outside the desirable range"
        temp_safe = False

    # 2. Electrical Conductivity
    ec = round(random.uniform(300, 3500), 2)

    if ec <= 750:
        ec_tag = "In the desirable range"
        ec_safe = True
    elif ec <= 3000:
        ec_tag = "Within the permissible reference range"
        ec_safe = True
    else:
        ec_tag = "Above the permissible reference range"
        ec_safe = False

    # 3. pH Level
    ph = round(random.uniform(5.5, 9.5), 2)

    if 6.5 <= ph <= 8.5:
        ph_tag = "In the desirable range"
        ph_safe = True
    else:
        ph_tag = "Outside the desirable range"
        ph_safe = False

    # 4. Colour
    colour = round(random.uniform(1, 20), 2)

    if colour <= 5:
        colour_tag = "In the desirable range"
        colour_safe = True
    elif colour <= 15:
        colour_tag = "Within the permissible range"
        colour_safe = True
    else:
        colour_tag = "Above the permissible range"
        colour_safe = False

    # 5. Dissolved Oxygen
    dissolved_oxygen = round(random.uniform(3, 9), 2)

    if dissolved_oxygen >= 6:
        do_tag = "Meets criterion"
        do_safe = True
    else:
        do_tag = "Below criterion"
        do_safe = False

    return {
        "temperature": {
            "value": temperature,
            "unit": "degree Celsius",
            "tag": temp_tag,
            "safe": temp_safe
        },
        "electrical_conductivity": {
            "value": ec,
            "unit": "µS/cm",
            "tag": ec_tag,
            "safe": ec_safe
        },
        "ph": {
            "value": ph,
            "unit": "pH",
            "tag": ph_tag,
            "safe": ph_safe
        },
        "colour": {
            "value": colour,
            "unit": "Hazen",
            "tag": colour_tag,
            "safe": colour_safe
        },
        "dissolved_oxygen": {
            "value": dissolved_oxygen,
            "unit": "mg/L",
            "tag": do_tag,
            "safe": do_safe
        },
        "generated_at": get_generated_at()
    }


async def sensor_loop():
    """Generate new sensor readings every 5 seconds."""
    global sensor_data

    while True:
        sensor_data = generate_readings()
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(sensor_loop())
    yield
    task.cancel()


app = FastAPI(
    title="Water Quality Sensor API",
    description="Simulated real-time water quality monitoring API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
def home():
    return {
        "message": "Water Quality Sensor API is running",
        "refresh_interval": "5 seconds",
        "endpoints": [
            "/temperature",
            "/ec",
            "/ph",
            "/colour",
            "/do",
            "/all"
        ]
    }


@app.get("/temperature")
def get_temperature():
    return {
        **sensor_data["temperature"],
        "generated_at": sensor_data["generated_at"]
    }


@app.get("/ec")
def get_electrical_conductivity():
    return {
        **sensor_data["electrical_conductivity"],
        "generated_at": sensor_data["generated_at"]
    }


@app.get("/ph")
def get_ph():
    return {
        **sensor_data["ph"],
        "generated_at": sensor_data["generated_at"]
    }


@app.get("/colour")
def get_colour():
    return {
        **sensor_data["colour"],
        "generated_at": sensor_data["generated_at"]
    }


@app.get("/do")
def get_dissolved_oxygen():
    return {
        **sensor_data["dissolved_oxygen"],
        "generated_at": sensor_data["generated_at"]
    }


@app.get("/all")
def get_all_readings():
    return sensor_data
