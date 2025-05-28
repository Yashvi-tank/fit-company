import os
from sqlalchemy import text
from ..database import engine, db_session
from ..models_db import UserModel
from ..services.user_service import hash_password


def init_fitness_data():
    """
    Initialize the fitness database with exercises + create default admin user.
    """
    try:
        # === 1. Run SQL script to init exercises ===
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sql_file_path = os.path.join(
            script_dir, "db_init_scripts", "init_muscle_groups_exercises.sql"
        )

        with open(sql_file_path, "r") as file:
            sql_script = file.read()

        with engine.connect() as connection:
            connection.execute(text(sql_script))
            connection.commit()

        print("✅ Fitness data initialized.")

        # === 2. Add default admin user if not present ===
        db = db_session()
        admin_email = "admin@example.com"
        existing_user = db.query(UserModel).filter_by(email=admin_email).first()

        if not existing_user:
            admin_user = UserModel(
                email=admin_email,
                password_hash=hash_password("admin123"),
                name="Admin User",
                role="admin",
            )

            db.add(admin_user)
            db.commit()
            print("✅ Admin user created.")
        else:
            print("ℹ️ Admin user already exists.")

        return True
    except Exception as e:
        print(f"❌ Error during fitness data initialization: {e}")
        return False


if __name__ == "__main__":
    init_fitness_data()
