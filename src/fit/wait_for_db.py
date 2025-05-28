import time
import psycopg2
import os

# Load DB env vars
host = os.getenv("DB_HOST", "db")
port = os.getenv("DB_PORT", 5432)
user = os.getenv("DB_USER", "postgres")
password = os.getenv("DB_PASSWORD", "docker")
dbname = os.getenv("DB_NAME", "postgres")

# Wait until DB is up
while True:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
        )
        conn.close()
        print(" Database is ready!")
        break
    except psycopg2.OperationalError:
        print("Waiting for database to be ready...")
        time.sleep(1)

# Start the actual Flask app after DB is ready
os.system("python -m src.fit.app")
