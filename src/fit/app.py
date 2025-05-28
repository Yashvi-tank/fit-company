from flask import Flask, request, jsonify, g
from pydantic import ValidationError
from .models_dto import UserSchema, UserResponseSchema, LoginSchema, TokenSchema, UserProfileSchema, UserProfileResponseSchema, WodResponseSchema, WodExerciseSchema, MuscleGroupImpact
from .services.user_service import create_user as create_user_service
from .services.user_service import get_all_users as get_all_users_service
from .services.user_service import update_user_profile, get_user_profile
from .services.auth_service import authenticate_user, create_access_token, admin_required, jwt_required
from .database import init_db, db_session
from .models_db import UserModel
from .services.fitness_data_init import init_fitness_data
from .services.fitness_service import (
    get_all_exercises, get_exercise_by_id, get_exercises_by_muscle_group
)
from .services.fitness_coach_service import calculate_intensity, request_wod
import datetime
import os
import random
import re
from datetime import date
from .models_db import UserExerciseHistoryModel
from .database import db_session
from .services.user_service import hash_password
from .models_db import UserExerciseHistoryModel


app = Flask(__name__)

BOOTSTRAP_KEY = os.environ.get("BOOTSTRAP_KEY", "bootstrap-secret-key")

@app.route("/health")
def health():
    return {"status": "UP"}

@app.route("/users", methods=["POST"])
@admin_required
def create_user():
    try:
        user_data = request.get_json()

        # Check required fields
        required_fields = ["email", "name", "role"]
        for field in required_fields:
            if field not in user_data:
                return jsonify({"error": f"'{field}' is required"}), 400

        # Validate email format
        def is_valid_email(email):
            return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

        if not is_valid_email(user_data["email"]):
            return jsonify({"error": "Invalid email format"}), 400

        # Validate role value
        if user_data["role"] not in ["user", "admin"]:
            return jsonify({"error": "Invalid role, must be 'user' or 'admin'"}), 400

        #  Validate against Pydantic schema
        user = UserSchema.model_validate(user_data)

        # Create user
        created_user = create_user_service(user)
        return jsonify(created_user.model_dump()), 201

    except ValidationError as e:
        return jsonify({"error": "Invalid user data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error creating user", "details": str(e)}), 500


@app.route("/users", methods=["GET"])
@admin_required
def get_all_users():
    try:
        users = get_all_users_service()
        return jsonify([user.model_dump() for user in users]), 200
    except Exception as e:
        return jsonify({"error": "Error retrieving users", "details": str(e)}), 500

@app.route("/bootstrap/admin", methods=["POST"])
def create_bootstrap_admin():
    try:
        bootstrap_key = request.headers.get('X-Bootstrap-Key')
        if not bootstrap_key or bootstrap_key != BOOTSTRAP_KEY:
            return jsonify({"error": "Invalid bootstrap key"}), 401

        db = db_session()
        admin_exists = db.query(UserModel).filter(UserModel.role == "admin").first() is not None
        db.close()

        if admin_exists:
            return jsonify({"error": "Admin user already exists"}), 409

        admin_data = request.get_json()
        plain_password = admin_data["password"]  
        hashed_password = hash_password(plain_password)

        db_user = UserModel(
            email=admin_data["email"],
            name=admin_data["name"],
            role="admin",
            password_hash=hashed_password
        )

        db = db_session()
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        db.close()

        return jsonify({
            "email": db_user.email,
            "name": db_user.name,
            "role": db_user.role,
            "login_password": plain_password
        }), 201

    except ValidationError as e:
        return jsonify({"error": "Invalid admin data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error creating admin", "details": str(e)}), 500


@app.route("/profile/onboarding", methods=["POST"])
@jwt_required
def onboard_user():
    try:
        # Get user email from the JWT token (set by the jwt_required decorator)
        user_email = g.user_email
        
        # Parse and validate the profile data
        profile_data = request.get_json()
        profile = UserProfileSchema.model_validate(profile_data)
        
        # Update the user's profile
        updated_profile = update_user_profile(user_email, profile)
        if not updated_profile:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify(updated_profile.model_dump()), 200
        
    except ValidationError as e:
        return jsonify({"error": "Invalid profile data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error updating profile", "details": str(e)}), 500

@app.route("/profile", methods=["GET"])
@jwt_required
def get_profile():
    try:
        # Get user email from the JWT token
        user_email = g.user_email
        
        # Get the user's profile
        profile = get_user_profile(user_email)
        if not profile:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify(profile.model_dump()), 200
        
    except Exception as e:
        return jsonify({"error": "Error retrieving profile", "details": str(e)}), 500

@app.route("/oauth/token", methods=["POST"])
def login():
    try:
        content_type = request.headers.get('Content-Type', '')
        print(f"[DEBUG] Content-Type: {content_type}")

        if 'application/x-www-form-urlencoded' in content_type:
            login_data = {
                "email": request.form.get("username"),
                "password": request.form.get("password")
            }
        else:
            login_data = request.get_json()

        print(f"[DEBUG] Login payload: {login_data}")

        login_schema = LoginSchema.model_validate(login_data)
        print(f"[DEBUG] Parsed login schema: {login_schema}")

        user = authenticate_user(login_schema.email, login_schema.password)

        if not user:
            print("[ERROR] Authentication failed: Invalid credentials")
            return jsonify({"error": "Invalid credentials"}), 401

        print(f"[DEBUG] Authenticated user: {user.email}")

        access_token_expires = datetime.timedelta(minutes=30)
        token_data = {
            "sub": user.email,
            "name": user.name,
            "role": user.role,
            "iss": "fit-api",
            "iat": datetime.datetime.now(datetime.UTC),
        }

        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )

        token = TokenSchema(
            access_token=access_token,
            token_type="bearer"
        )

        response_data = token.model_dump()
        response_data["onboarded"] = user.onboarded

        print(f"[DEBUG] Token response: {response_data}")
        return jsonify(response_data), 200

    except ValidationError as e:
        print(f"[ERROR] Validation error: {e.errors()}")
        return jsonify({"error": "Invalid login data", "details": e.errors()}), 400
    except Exception as e:
        print(f"[ERROR] Unexpected exception: {str(e)}")
        return jsonify({"error": "Error logging in", "details": str(e)}), 500


@app.route("/fitness/exercises", methods=["GET"])
def get_exercises():
    try:
        muscle_group_id = request.args.get("muscle_group_id")
        if muscle_group_id:
            # Get exercises for a specific muscle group
            exercises = get_exercises_by_muscle_group(int(muscle_group_id))
        else:
            # Get all exercises
            exercises = get_all_exercises()
        return jsonify([ex.model_dump() for ex in exercises]), 200
    except Exception as e:
        return jsonify({"error": "Error retrieving exercises", "details": str(e)}), 500

@app.route("/fitness/exercises/<int:exercise_id>", methods=["GET"])
def get_exercise(exercise_id):
    try:
        exercise = get_exercise_by_id(exercise_id)
        if not exercise:
            return jsonify({"error": "Exercise not found"}), 404
        return jsonify(exercise.model_dump()), 200
    except Exception as e:
        return jsonify({"error": "Error retrieving exercise", "details": str(e)}), 500

@app.route("/fitness/wod", methods=["GET"])
@jwt_required
def get_wod():
    try:
        # Get the workout exercises with their muscle groups
        exercises_with_muscles = request_wod()
        
        # Convert to response schema
        wod_exercises = []
        for exercise, muscle_groups in exercises_with_muscles:
            # Create muscle group impact objects
            muscle_impacts = [
                MuscleGroupImpact(
                    id=mg.id,
                    name=mg.name,
                    body_part=mg.body_part,
                    is_primary=is_primary,
                    # Higher intensity for primary muscle groups
                    intensity=calculate_intensity(exercise.difficulty) * (1.2 if is_primary else 0.8)
                )
                for mg, is_primary in muscle_groups
            ]
            
            # Create exercise object
            wod_exercise = WodExerciseSchema(
                id=exercise.id,
                name=exercise.name,
                description=exercise.description,
                difficulty=exercise.difficulty,
                muscle_groups=muscle_impacts,
                suggested_weight=random.uniform(5.0, 50.0),  # Random weight between 5 and 50 kg
                suggested_reps=random.randint(8, 15)  # Random reps between 8 and 15
            )
            wod_exercises.append(wod_exercise)
        
        response = WodResponseSchema(
            exercises=wod_exercises,
            generated_at=datetime.datetime.now(datetime.UTC).isoformat()
        )

        # Save WOD to history
        db = db_session()
        try:
            for exercise in wod_exercises:
                history_entry = UserExerciseHistoryModel(
                    user_email=g.user_email,
                    exercise_id=exercise.id,
                    date_assigned=date.today()
                )
                db.add(history_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            print("Error saving exercise history:", e)
        finally:
            db.close()

        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        return jsonify({"error": "Error generating workout of the day", "details": str(e)}), 500
    
@app.route("/history", methods=["GET"])
@jwt_required
def get_exercise_history():
    try:
        db = db_session()
        history = (
            db.query(UserExerciseHistoryModel)
            .filter(UserExerciseHistoryModel.user_email == g.user_email)
            .order_by(UserExerciseHistoryModel.date_assigned.desc())
            .all()
        )

        history_data = [
            {
                "exercise_id": record.exercise_id,
                "date_assigned": record.date_assigned.isoformat()
            }
            for record in history
        ]
        return jsonify({"history": history_data}), 200

    except Exception as e:
        return jsonify({"error": "Could not retrieve history", "details": str(e)}), 500
    finally:
        db.close()


def run_app():
    """Entry point for the application script"""
    # Initialize the database before starting the app
    init_db()
    
    # Initialize fitness data
    init_fitness_data()
    
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run_app()

