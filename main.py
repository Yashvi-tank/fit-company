from src.fit.app import run_app
from src.fit.wait_for_db import wait_for_db

if __name__ == "__main__":
    wait_for_db()
    run_app()
