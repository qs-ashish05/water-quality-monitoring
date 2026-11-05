
import requests
import psycopg2
import time

from datetime import datetime
from zoneinfo import ZoneInfo
from psycopg2 import sql


# ==========================================
# 1. CONFIGURATION
# ==========================================

API_BASE_URL = "http://127.0.0.1:8000"

DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "admin"
DB_PASSWORD = "admin123"

SOURCE_DATABASE = "pg1"
TARGET_DATABASE = "dataEngineering"

COLLECTION_INTERVAL = 5


# ==========================================
# 2. CREATE DATABASE
# ==========================================

def create_database():

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=SOURCE_DATABASE,
        user=DB_USER,
        password=DB_PASSWORD
    )

    conn.autocommit = True

    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (TARGET_DATABASE,)
    )

    if cursor.fetchone() is None:

        cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(TARGET_DATABASE)
            )
        )

        print(f"Database '{TARGET_DATABASE}' created.")

    else:
        print(f"Database '{TARGET_DATABASE}' already exists.")

    cursor.close()
    conn.close()


# ==========================================
# 3. CONNECT TO TARGET DATABASE
# ==========================================

def get_db_connection():

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=TARGET_DATABASE,
        user=DB_USER,
        password=DB_PASSWORD
    )


# ==========================================
# 4. CREATE TABLE
# ==========================================

def create_table(conn):

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS real_time_data (

            id SERIAL PRIMARY KEY,

            temperature FLOAT,
            temperature_unit VARCHAR(30),
            temperature_tag VARCHAR(100),
            temperature_safe BOOLEAN,

            electrical_conductivity FLOAT,
            ec_unit VARCHAR(20),
            ec_tag VARCHAR(100),
            ec_safe BOOLEAN,

            ph FLOAT,
            ph_tag VARCHAR(100),
            ph_safe BOOLEAN,

            colour FLOAT,
            colour_unit VARCHAR(20),
            colour_tag VARCHAR(100),
            colour_safe BOOLEAN,

            dissolved_oxygen FLOAT,
            do_unit VARCHAR(20),
            do_tag VARCHAR(100),
            do_safe BOOLEAN,

            generated_at TIMESTAMP,
            collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cursor.close()

    print("Table 'real_time_data' is ready.")


# ==========================================
# 5. FETCH SENSOR DATA FROM FASTAPI
# ==========================================

def fetch_sensor_data():

    endpoints = {
        "temperature": "/temperature",
        "ec": "/ec",
        "ph": "/ph",
        "colour": "/colour",
        "do": "/do"
    }

    readings = {}

    for parameter, endpoint in endpoints.items():

        response = requests.get(
            API_BASE_URL + endpoint,
            timeout=3
        )

        response.raise_for_status()

        readings[parameter] = response.json()

    return readings


# ==========================================
# 6. INSERT DATA INTO POSTGRESQL
# ==========================================

def insert_data(conn, readings):

    cursor = conn.cursor()

    temperature = readings["temperature"]
    ec = readings["ec"]
    ph = readings["ph"]
    colour = readings["colour"]
    do = readings["do"]

    # Extract generated timestamp
    generated = temperature["generated_at"]

    # Convert Indian date and time into Python datetime
    generated_at = datetime.strptime(
        f'{generated["Date"]} {generated["Time"]}',
        "%d-%m-%Y %H:%M:%S"
    )

    # Validate that all five endpoints belong to
    # the same sensor generation cycle.
    for parameter, reading in readings.items():

        if reading["generated_at"] != generated:
            raise ValueError(
                f"Inconsistent sensor timestamp: {parameter}"
            )

    query = """
        INSERT INTO real_time_data (

            temperature,
            temperature_unit,
            temperature_tag,
            temperature_safe,

            electrical_conductivity,
            ec_unit,
            ec_tag,
            ec_safe,

            ph,
            ph_tag,
            ph_safe,

            colour,
            colour_unit,
            colour_tag,
            colour_safe,

            dissolved_oxygen,
            do_unit,
            do_tag,
            do_safe,

            generated_at
        )

        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    values = (

        temperature["value"],
        temperature["unit"],
        temperature["tag"],
        temperature["safe"],

        ec["value"],
        ec["unit"],
        ec["tag"],
        ec["safe"],

        ph["value"],
        ph["unit"],
        ph["tag"],
        ph["safe"],

        colour["value"],
        colour["unit"],
        colour["tag"],
        colour["safe"],

        do["value"],
        do["unit"],
        do["tag"],
        do["safe"],

        generated_at
    )

    cursor.execute(query, values)

    conn.commit()
    cursor.close()

    print("Data inserted successfully!")


# ==========================================
# 7. MAIN COLLECTION LOOP
# ==========================================

def main():

    create_database()

    conn = get_db_connection()

    create_table(conn)

    print("\nWater Quality Data Ingestion Started")
    print("Collection interval: 5 seconds\n")

    try:

        while True:

            start_time = time.monotonic()

            try:

                readings = fetch_sensor_data()

                insert_data(conn, readings)

                print(
                    f"Temperature: {readings['temperature']['value']} °C | "
                    f"EC: {readings['ec']['value']} µS/cm | "
                    f"pH: {readings['ph']['value']} | "
                    f"Colour: {readings['colour']['value']} HU | "
                    f"DO: {readings['do']['value']} mg/L"
                )

                print("-" * 70)

            except requests.RequestException as error:

                print("API connection error:", error)

            except (ValueError, KeyError) as error:

                print("Data validation error:", error)

            except psycopg2.Error as error:

                print("Database error:", error)

                if conn.closed:
                    conn = get_db_connection()

            # Maintain a 5-second collection interval
            elapsed = time.monotonic() - start_time

            sleep_time = max(
                0,
                COLLECTION_INTERVAL - elapsed
            )

            time.sleep(sleep_time)

    except KeyboardInterrupt:

        print("\nData ingestion stopped by user.")

    finally:

        if not conn.closed:
            conn.close()


# ==========================================
# 8. EXECUTION
# ==========================================

if __name__ == "__main__":
    main()
