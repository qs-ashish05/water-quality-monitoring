import logging
import os
import time
from datetime import datetime, timedelta, timezone

import psycopg2
import requests

# config ---
API_URL = "http://127.0.0.1:8000/all"
POLL_INTERVAL_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 4

DB_CONFIG = {
    "host": "aws-0-ap-south-1.pooler.supabase.com",
    "port":  6543,
    "dbname": "postgres",
    "user": "postgres.jrcnplryqsgwflsytxyc",
    "password": "test@1234",
}

# The API timestamps are in IST (UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30))

INSERT_SQL = """
    INSERT INTO water_quality (
        generated_at,
        temperature, temperature_tag, temperature_safe,
        conductivity, conductivity_tag, conductivity_safe,
        ph, ph_tag, ph_safe,
        colour, colour_tag, colour_safe,
        dissolved_oxygen, do_tag, do_safe
    ) VALUES (
        %(generated_at)s,
        %(temperature)s, %(temperature_tag)s, %(temperature_safe)s,
        %(conductivity)s, %(conductivity_tag)s, %(conductivity_safe)s,
        %(ph)s, %(ph_tag)s, %(ph_safe)s,
        %(colour)s, %(colour_tag)s, %(colour_safe)s,
        %(dissolved_oxygen)s, %(do_tag)s, %(do_safe)s
    )
    ON CONFLICT (generated_at) DO NOTHING;
"""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("water_quality")


# --------------------------------------------------------------- helpers ---
def fetch_data():
    """Call the API and return the parsed JSON."""
    response = requests.get(API_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def parse_row(data):
    """Convert the API JSON into a flat dict matching the table columns."""
    ts = data["generated_at"]
    generated_at = datetime.strptime(
        f"{ts['Date']} {ts['Time']}", "%d-%m-%Y %H:%M:%S"
    ).replace(tzinfo=IST)

    return {
        "generated_at": generated_at,
        "temperature": data["temperature"]["value"],
        "temperature_tag": data["temperature"]["tag"],
        "temperature_safe": data["temperature"]["safe"],
        "conductivity": data["electrical_conductivity"]["value"],
        "conductivity_tag": data["electrical_conductivity"]["tag"],
        "conductivity_safe": data["electrical_conductivity"]["safe"],
        "ph": data["ph"]["value"],
        "ph_tag": data["ph"]["tag"],
        "ph_safe": data["ph"]["safe"],
        "colour": data["colour"]["value"],
        "colour_tag": data["colour"]["tag"],
        "colour_safe": data["colour"]["safe"],
        "dissolved_oxygen": data["dissolved_oxygen"]["value"],
        "do_tag": data["dissolved_oxygen"]["tag"],
        "do_safe": data["dissolved_oxygen"]["safe"],
    }


def connect_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    log.info("Connected to PostgreSQL at %s:%s",
             DB_CONFIG["host"], DB_CONFIG["port"])
    return conn


def insert_row(conn, row):
    """Insert one row. Returns True if inserted, False if it was a duplicate."""
    with conn.cursor() as cur:
        cur.execute(INSERT_SQL, row)
        inserted = cur.rowcount == 1
    conn.commit()
    return inserted


# ------------------------------------------------------------------ main ---
def main():
    conn = None
    log.info("Starting collector: %s every %ss",
             API_URL, POLL_INTERVAL_SECONDS)

    try:
        while True:
            cycle_start = time.monotonic()

            try:
                # (Re)connect to the database if needed
                if conn is None or conn.closed:
                    conn = connect_db()

                data = fetch_data()
                row = parse_row(data)

                if insert_row(conn, row):
                    log.info(
                        "Inserted reading for %s | temp=%.2f ph=%.2f DO=%.2f",
                        row["generated_at"].isoformat(),
                        row["temperature"],
                        row["ph"],
                        row["dissolved_oxygen"],
                    )
                else:
                    log.info(
                        "Skipped duplicate reading for %s (already stored)",
                        row["generated_at"].isoformat(),
                    )

            except requests.RequestException as exc:
                log.error("API request failed: %s", exc)
            except (KeyError, ValueError, TypeError) as exc:
                log.error("Unexpected API data format: %r", exc)
            except psycopg2.Error as exc:
                log.error("Database error: %s", exc)
                try:
                    if conn is not None and not conn.closed:
                        conn.rollback()
                        conn.close()
                except Exception:
                    pass
                conn = None  # force reconnect on next cycle

            # Sleep for the remainder of the 5-second window
            elapsed = time.monotonic() - cycle_start
            time.sleep(max(0, POLL_INTERVAL_SECONDS - elapsed))

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    finally:
        if conn is not None and not conn.closed:
            conn.close()
            log.info("Database connection closed.")


if __name__ == "__main__":
    main()
